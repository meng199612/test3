# Pic2PointCloud

上传多张图片 → 自动生成 3D 点云 → 浏览器交互查看

## 技术栈
- **后端**: Python FastAPI + OpenCV + Open3D + SciPy
- **前端**: Vue 3 + Vite + Three.js
- **核心算法**: 自制 SfM 管线（SIFT → FLANN → 增量式SfM → BA → 点云后处理）

## 环境要求
- Python 3.9+
- Node.js 18+

## 快速开始

### 1. 安装后端依赖
```bash
pip install -r backend/requirements.txt
```

### 2. 安装前端依赖
```bash
cd frontend && npm install && cd ..
```

### 3. 启动后端
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. 启动前端（新终端）
```bash
cd frontend && npx vite --port 5173
```

### 5. 打开浏览器
访问 http://localhost:5173

## 使用说明
1. 拖拽或选择 2-50 张围绕物体拍摄的图片
2. 点击"开始生成 3D"
3. 等待后端处理完成（10-50张图约需几十秒到几分钟）
4. 在浏览器中旋转/缩放查看 3D 点云
5. 点击"下载 PLY"获取完整的点云文件

## 项目结构

```
ts5/
├── backend/
│   ├── __init__.py
│   ├── config.py              # 配置项
│   ├── main.py                # FastAPI 入口
│   ├── requirements.txt       # Python 依赖
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── upload.py          # 图片上传路由
│   │   ├── reconstruct.py     # 重建路由 + WebSocket
│   │   └── download.py        # 下载 + Session 管理
│   └── services/
│       ├── __init__.py
│       └── sfm/
│           ├── __init__.py
│           ├── feature.py     # SIFT 特征提取
│           ├── matching.py    # FLANN 特征匹配
│           ├── reconstruction.py  # 增量式 SfM
│           ├── bundle_adjust.py   # 光束法平差
│           ├── pointcloud.py  # 点云后处理 + PLY 导出
│           └── pipeline.py    # SfM 管线编排
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.js
        ├── App.vue
        ├── router/
        │   └── index.js
        ├── views/
        │   ├── UploadPage.vue
        │   ├── ProcessingPage.vue
        │   └── ViewerPage.vue
        └── components/
            └── PointCloudViewer.vue
```

## 算法流程

1. **特征提取**: 使用 OpenCV SIFT 提取每张图片的关键点和描述子
2. **特征匹配**: 相邻帧之间使用 FLANN 匹配 + Lowe's Ratio Test 过滤误匹配
3. **增量式 SfM**:
   - 选择匹配最多的相邻对作为初始帧
   - 本质矩阵估计 → 恢复相对位姿 → 三角测量初始 3D 点
   - 逐张注册剩余图片（PnP + 三角测量新点）
4. **光束法平差 (BA)**: 使用 SciPy least_squares 优化相机位姿和 3D 点
5. **点云后处理**:
   - 从图片采样颜色
   - 统计滤波去除离群点
   - 体素降采样
   - 导出 PLY 和 JSON
