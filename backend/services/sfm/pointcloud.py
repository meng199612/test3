import open3d as o3d
import numpy as np
import json
import os
from backend.logger import get_logger

logger = get_logger(__name__)


def filter_pointcloud(points_3d, colors=None):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points_3d)
    if colors is not None:
        pcd.colors = o3d.utility.Vector3dVector(colors)
    if len(pcd.points) > 50:
        pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
    return pcd


def export_ply(pcd, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    o3d.io.write_point_cloud(output_path, pcd, write_ascii=False)
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        logger.info(f"[导出] PLY文件已保存: {output_path} ({file_size / 1024:.1f} KB)")
    else:
        logger.warning(f"[导出] 警告: PLY文件未能保存到 {output_path}")


def simplify_for_web(pcd, max_points=50000):
    n_points = len(pcd.points)
    if n_points == 0:
        return {"vertices": [], "n_points": 0}
    if n_points > max_points:
        bounds = pcd.get_axis_aligned_bounding_box()
        extent = bounds.get_max_bound() - bounds.get_min_bound()
        avg_extent = np.mean(extent) if np.mean(extent) > 0 else 1.0
        voxel_size = avg_extent / (max_points ** (1/3)) * 2
        pcd_simple = pcd.voxel_down_sample(max(voxel_size, 0.01))
    else:
        pcd_simple = pcd
    points = np.asarray(pcd_simple.points)
    colors = np.asarray(pcd_simple.colors)
    if colors.shape[0] > 0 and colors.shape[0] == points.shape[0]:
        colors_255 = (np.clip(colors, 0, 1) * 255).astype(np.uint8)
    else:
        colors_255 = np.full((points.shape[0], 3), 128, dtype=np.uint8)
    vertices = []
    for i in range(len(points)):
        vertices.append([
            float(points[i, 0]), float(points[i, 1]), float(points[i, 2]),
            int(colors_255[i, 0]), int(colors_255[i, 1]), int(colors_255[i, 2])
        ])
    return {"vertices": vertices, "n_points": len(vertices)}


def generate_display_data(pcd, max_points=50000):
    return simplify_for_web(pcd, max_points)
