import os
import numpy as np
import json
import cv2
from backend.services.sfm.feature import extract_all_features
from backend.services.sfm.matching import match_adjacent_pairs
from backend.services.sfm.reconstruction import IncrementalSfM
from backend.services.sfm.bundle_adjust import bundle_adjust
from backend.services.sfm.pointcloud import filter_pointcloud, export_ply, generate_display_data


class SfMPipeline:
    def __init__(self, image_dir, session_dir, progress_callback=None, K=None):
        self.image_dir = image_dir
        self.session_dir = session_dir
        self.progress = progress_callback or (lambda p, m: None)
        self.K = K

    def _make_K(self, img_shape):
        h, w = img_shape[:2]
        K = np.array([
            [max(w, h) * 1.2, 0, w / 2],
            [0, max(w, h) * 1.2, h / 2],
            [0, 0, 1]
        ], dtype=np.float64)
        return K

    def run(self):
        self.progress(5, "正在提取 SIFT 特征...")
        features = extract_all_features(self.image_dir)

        first_img_path = os.path.join(self.image_dir, sorted(os.listdir(self.image_dir))[0])
        first_img = cv2.imread(first_img_path)
        K = self.K if self.K is not None else self._make_K(first_img.shape)

        self.progress(20, "正在匹配特征点...")
        match_pairs = match_adjacent_pairs(features)

        if not match_pairs:
            raise RuntimeError("特征匹配失败，没有足够的匹配对")

        self.progress(35, "正在进行增量式三维重建...")
        sfm = IncrementalSfM(K)
        points_3d, camera_poses = sfm.run(self.image_dir, features, match_pairs)

        if len(points_3d) < 10:
            raise RuntimeError(f"重建失败: 仅生成 {len(points_3d)} 个3D点")

        self.progress(60, "正在进行光束法平差优化...")
        observations = []
        for cam_idx, fn in enumerate(sfm.registered):
            for pt_idx, pt in enumerate(points_3d[:100]):
                observations.append((cam_idx, pt_idx, float(pt[0]), float(pt[1])))

        if len(observations) >= 10 and len(points_3d) >= 10:
            try:
                points_3d, camera_poses = bundle_adjust(
                    points_3d, camera_poses, observations[:min(len(observations), 500)], K
                )
            except Exception as e:
                print(f"[BA] 跳过BA优化: {e}")

        self.progress(75, "正在采样点云颜色...")
        colors = self._sample_colors(points_3d, sfm)

        self.progress(85, "正在进行点云后处理...")
        pcd = filter_pointcloud(points_3d, colors)

        ply_path = os.path.join(self.session_dir, "result.ply")
        export_ply(pcd, ply_path)

        self.progress(95, "正在生成Web展示数据...")
        display_data = generate_display_data(pcd)

        json_path = os.path.join(self.session_dir, "result_simple.json")
        with open(json_path, 'w') as f:
            json.dump(display_data, f)

        self.progress(100, "完成!")
        return {
            "ply_path": ply_path,
            "json_path": json_path,
            "n_points": len(points_3d),
            "n_registered": len(sfm.registered),
            "n_cameras": len(camera_poses)
        }

    def _sample_colors(self, points_3d, sfm):
        n = len(points_3d)
        colors = np.ones((n, 3)) * 0.5
        if n == 0 or not sfm.registered:
            return colors

        first_fn = sfm.registered[0]
        img_path = os.path.join(self.image_dir, first_fn)
        if not os.path.exists(img_path):
            return colors

        img = cv2.imread(img_path)
        if img is None:
            return colors
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]

        R, t = sfm.camera_poses[first_fn]
        K = sfm.K

        for i, pt in enumerate(points_3d):
            pt_cam = R @ pt.reshape(3, 1) + t
            if pt_cam[2] <= 1e-6:
                continue
            u = int(K[0, 0] * pt_cam[0] / pt_cam[2] + K[0, 2])
            v = int(K[1, 1] * pt_cam[1] / pt_cam[2] + K[1, 2])
            if 0 <= u < w and 0 <= v < h:
                colors[i] = img_rgb[v, u] / 255.0

        return colors
