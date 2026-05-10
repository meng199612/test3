import numpy as np
import cv2
from scipy.optimize import least_squares
from backend.logger import get_logger

logger = get_logger(__name__)


def reprojection_error(params, n_cameras, n_points, observations, K):
    camera_params = params[:n_cameras * 6].reshape(n_cameras, 6)
    point_params = params[n_cameras * 6:].reshape(n_points, 3)

    errors = []
    for obs in observations:
        cam_idx, pt_idx, u, v = obs
        R_vec = camera_params[cam_idx, :3]
        t = camera_params[cam_idx, 3:].reshape(3, 1)
        pt = point_params[pt_idx].reshape(3, 1)

        theta = np.linalg.norm(R_vec)
        if theta < 1e-10:
            R = np.eye(3)
        else:
            k = R_vec / theta
            K_mat = np.array([[0, -k[2], k[1]],
                              [k[2], 0, -k[0]],
                              [-k[1], k[0], 0]])
            R = np.eye(3) + np.sin(theta) * K_mat + (1 - np.cos(theta)) * (K_mat @ K_mat)

        pt_cam = R @ pt + t
        if pt_cam[2] <= 1e-6:
            errors.append(1000.0)
            errors.append(1000.0)
            continue
        u_proj = K[0, 0] * pt_cam[0] / pt_cam[2] + K[0, 2]
        v_proj = K[1, 1] * pt_cam[1] / pt_cam[2] + K[1, 2]

        errors.append(u_proj - u)
        errors.append(v_proj - v)

    return np.array(errors)


def bundle_adjust(points_3d, camera_poses, observations, K):
    n_cameras = len(camera_poses)
    n_points = len(points_3d)
    if n_points == 0 or n_cameras < 2:
        return points_3d, camera_poses

    camera_params = []
    camera_list = sorted(camera_poses.keys())
    for fn in camera_list:
        R, t = camera_poses[fn]
        R_vec, _ = cv2.Rodrigues(R)
        camera_params.extend(R_vec.flatten())
        camera_params.extend(t.flatten())

    init_params = np.hstack([camera_params, points_3d.flatten()])

    result = least_squares(
        reprojection_error, init_params,
        args=(n_cameras, n_points, observations, K),
        method='lm', max_nfev=100, verbose=0
    )

    opt_camera_params = result.x[:n_cameras * 6].reshape(n_cameras, 6)
    opt_points = result.x[n_cameras * 6:].reshape(n_points, 3)

    for i, fn in enumerate(camera_list):
        R_vec = opt_camera_params[i, :3]
        theta = np.linalg.norm(R_vec)
        if theta < 1e-10:
            R = np.eye(3)
        else:
            k = R_vec / theta
            K_mat = np.array([[0, -k[2], k[1]],
                              [k[2], 0, -k[0]],
                              [-k[1], k[0], 0]])
            R = np.eye(3) + np.sin(theta) * K_mat + (1 - np.cos(theta)) * (K_mat @ K_mat)
        t = opt_camera_params[i, 3:].reshape(3, 1)
        camera_poses[fn] = (R, t)

    error_before = np.mean(np.abs(reprojection_error(init_params, n_cameras, n_points, observations, K)))
    error_after = np.mean(np.abs(result.fun))
    logger.info(f"[BA] 平均重投影误差: {error_before:.2f}px → {error_after:.2f}px")

    return opt_points, camera_poses
