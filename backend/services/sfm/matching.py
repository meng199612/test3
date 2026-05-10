import cv2
import numpy as np


def match_features(desc1, desc2, ratio_thresh=0.75):
    if desc1.shape[0] == 0 or desc2.shape[0] == 0:
        return []
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(desc1, desc2, k=2)
    good_matches = []
    for m, n in matches:
        if m.distance < ratio_thresh * n.distance:
            good_matches.append(m)
    return good_matches


def match_adjacent_pairs(features_dict: dict) -> list:
    filenames = sorted(features_dict.keys())
    pairs = []
    for i in range(len(filenames) - 1):
        f1, f2 = filenames[i], filenames[i+1]
        kp1, d1 = features_dict[f1]
        kp2, d2 = features_dict[f2]
        matches = match_features(d1, d2)
        pairs.append((f1, f2, matches, kp1, kp2))
        print(f"[特征匹配] {f1} ↔ {f2} - 有效匹配 {len(matches)} 对")
        if len(matches) < 20:
            print(f"  ⚠️ 警告: 匹配对数偏少 ({len(matches)}), 可能影响重建")
    return pairs
