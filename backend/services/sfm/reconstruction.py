import cv2
import numpy as np
from pathlib import Path
import os
from backend.logger import get_logger

logger = get_logger(__name__)


class IncrementalSfM:
    def __init__(self, K):
        self.K = K
        self.camera_poses = {}
        self.points_3d = []
        self.point_colors = []
        self.registered = []
        self._point_to_kp = []

    def estimate_relative_pose(self, kp1, kp2, matches):
        pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
        pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])
        if len(pts1) < 8:
            return None, None, None, pts1, pts2
        E, mask = cv2.findEssentialMat(pts1, pts2, self.K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
        if E is None or E.shape[0] != 3:
            return None, None, None, pts1, pts2
        _, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, self.K)
        inliers = [m for i, m in enumerate(matches) if mask[i] > 0 and i < len(mask_pose) and mask_pose[i] > 0]
        return R, t, inliers, pts1, pts2

    def triangulate_points(self, kp1, kp2, matches, P1, P2):
        pts1 = np.float32([kp1[m.queryIdx].pt for m in matches]).T
        pts2 = np.float32([kp2[m.trainIdx].pt for m in matches]).T
        pts4d = cv2.triangulatePoints(P1, P2, pts1, pts2)
        pts3d = (pts4d[:3] / pts4d[3]).T
        return pts3d

    def get_pnp_pose(self, points_3d, points_2d, K):
        _, rvec, tvec, inliers = cv2.solvePnPRansac(
            points_3d, points_2d, K, None, iterationsCount=100, reprojectionError=8.0, confidence=0.99
        )
        if inliers is None or len(inliers) < 4:
            return None, None, None
        R, _ = cv2.Rodrigues(rvec)
        return R, tvec, inliers

    def register_image(self, new_filename, kp_new, features_dict, match_pairs):
        points_3d_list = []
        points_2d_list = []
        for reg_fn in self.registered:
            pair = next((p for p in match_pairs
                        if (p[0] == reg_fn and p[1] == new_filename)
                        or (p[1] == reg_fn and p[0] == new_filename)), None)
            if pair is None:
                continue
            f1, f2, matches, kp1, kp2 = pair
            kp_a = kp1 if f1 == reg_fn else kp2
            kp_b = kp2 if f1 == reg_fn else kp1
            for m in matches:
                pt3d_idx = None
                kp_a_idx = m.queryIdx if f1 == reg_fn else m.trainIdx
                for pt_idx, pt in enumerate(self.points_3d):
                    if pt_idx < len(self._point_to_kp) and self._point_to_kp[pt_idx] == (reg_fn, kp_a_idx):
                        pt3d_idx = pt_idx
                        break
                if pt3d_idx is not None:
                    points_3d_list.append(self.points_3d[pt3d_idx])
                    kp_b_idx = m.trainIdx if f1 == reg_fn else m.queryIdx
                    points_2d_list.append(kp_b[kp_b_idx].pt)
        if len(points_3d_list) < 4:
            logger.warning(f"  ⚠️ 无法注册 {new_filename}: 仅 {len(points_3d_list)} 个对应点")
            return False

        pts_3d = np.float32(points_3d_list)
        pts_2d = np.float32(points_2d_list)
        R, t, inliers = self.get_pnp_pose(pts_3d, pts_2d, self.K)
        if R is None:
            logger.warning(f"  ⚠️ 无法注册 {new_filename}: PnP失败")
            return False

        self.camera_poses[new_filename] = (R, t)
        self.registered.append(new_filename)

        last_fn = self.registered[-2] if len(self.registered) >= 2 else None
        if last_fn:
            pair = next((p for p in match_pairs
                        if (p[0] == last_fn and p[1] == new_filename)
                        or (p[1] == last_fn and p[0] == new_filename)), None)
            if pair:
                f1, f2, matches, kp1, kp2 = pair
                kp_a = kp1 if f1 == last_fn else kp2
                kp_b = kp2 if f1 == last_fn else kp1
                R1, t1 = self.camera_poses[last_fn]
                R2, t2 = self.camera_poses[new_filename]
                P1 = self.K @ np.hstack((R1, t1))
                P2 = self.K @ np.hstack((R2, t2))
                new_pts = self.triangulate_points(kp_a, kp_b, matches, P1, P2)
                for pt in new_pts:
                    if pt[2] > 0:
                        self.points_3d.append(pt)
        logger.info(f"[增量SfM] 注册 {new_filename} - 已有 {len(self.points_3d)} 个3D点")
        return True

    def run(self, image_dir, features_dict, match_pairs):
        best_pair = max(match_pairs, key=lambda p: len(p[2]))
        f1, f2, matches, kp1, kp2 = best_pair

        R, t, inliers, pts1, pts2 = self.estimate_relative_pose(kp1, kp2, matches)
        if R is None:
            raise RuntimeError("Failed to estimate initial relative pose")

        P1 = self.K @ np.hstack((np.eye(3), np.zeros((3, 1))))
        P2 = self.K @ np.hstack((R, t))

        self.camera_poses[f1] = (np.eye(3), np.zeros((3, 1)))
        self.camera_poses[f2] = (R, t)
        self.registered = [f1, f2]

        filtered_matches = inliers
        pts3d = self.triangulate_points(kp1, kp2, filtered_matches, P1, P2)
        self.points_3d = [pt for pt in pts3d if pt[2] > 0]
        self._point_to_kp = [(f1, m.queryIdx) for m in filtered_matches[:len(self.points_3d)]]

        logger.info(f"[增量SfM] 初始对: {f1} ↔ {f2} - {len(self.points_3d)} 个3D点")

        remaining = [fn for fn in sorted(features_dict.keys())
                    if fn not in self.registered]
        for fn in remaining:
            kp = features_dict[fn][0]
            self.register_image(fn, kp, features_dict, match_pairs)

        points_3d = np.array(self.points_3d) if self.points_3d else np.zeros((0, 3))
        logger.info(f"[增量SfM] 完成: {len(self.registered)} 张注册, {points_3d.shape[0]} 个3D点")
        return points_3d, self.camera_poses
