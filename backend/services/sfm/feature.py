import cv2
import numpy as np
from pathlib import Path
import os
from backend.logger import get_logger

logger = get_logger(__name__)


def extract_features(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sift = cv2.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(gray, None)
    if descriptors is None:
        return [], np.array([], dtype=np.float32).reshape(0, 128)
    return keypoints, descriptors.astype(np.float32)


def extract_all_features(image_dir: str) -> dict:
    image_extensions = {'.jpg', '.jpeg', '.png'}
    image_files = sorted([
        f for f in os.listdir(image_dir)
        if Path(f).suffix.lower() in image_extensions
    ])
    if not image_files:
        raise ValueError(f"No image files found in {image_dir}")
    features = {}
    for filename in image_files:
        filepath = os.path.join(image_dir, filename)
        kp, desc = extract_features(filepath)
        features[filename] = (kp, desc)
        logger.info(f"[特征提取] {filename} - 找到 {len(kp)} 个关键点")
    return features
