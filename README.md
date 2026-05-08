# YOLO 视觉检测系统

这是一个中文化、通用化、可复用的 YOLOv8 目标检测 Web 系统，面向图片、批量图片、视频文件和实时视频流检测场景。系统不绑定车辆、鱼类、工业缺陷等具体业务，替换模型和类别映射后即可复用到新的目标检测项目。

## 功能特性

- YOLOv8 工程化封装：单例加载、GPU/CPU/自动设备切换、模型热切换、线程安全推理
- 检测入口：单图检测、批量图片检测、视频异步检测、实时摄像头/RTSP/HTTP(S) 流检测
- 检测参数：置信度阈值、IoU 阈值、保存到历史记录或仅本地临时检测
- 检测展示：原图/检测图对比、视频帧流、检测后本地视频、目标结果表格、不同类别检测框自动分色
- 任务控制：批量图片、视频文件、实时视频流支持开始、暂停/继续、结束和进度反馈
- 历史管理：缩略图、视频第一帧、检测详情、中文类别查询、用户查询、Excel 导出、全选批量删除
- 视频回放：历史详情优先播放后端 artifact mp4，不暴露本地磁盘路径；支持 HTTP Range，旧 FMP4/mp4v 视频会自动生成 H.264 `_browser.mp4` 兼容副本，仍无法解码时切换为帧流兜底
- 模型管理：模型上传、登记路径必填校验、前端连续序号展示、完整路径换行展示、激活模型、删除非激活模型、修改显示名称、GPU 设备切换、类别中英文映射维护
- 权限系统：登录、注册、简单忘记密码、JWT、用户、角色、权限码、RBAC 路由守卫
- 用户管理：用户查询、新建用户、启用/停用、角色维护、重置密码、创建时间和最后登录时间展示
- Dashboard：检测统计、类别分布、趋势图；管理员可查看用户数、模型数、异常日志数、AI 调用次数、CPU/内存/GPU/温度状态和 CUDA 诊断
- 日志中心：级别、模块、类型中文化展示，支持单条删除、批量删除和按日期删除
- 训练分析：上传或选择 YOLO `results.csv`，绘制 Precision/Recall、mAP、Loss、学习率曲线，生成雷达图、柱状图、导出分析报告、删除当前分析、清空全部分析和 AI 训练诊断
- 系统维护：检查 GPU/CUDA/torch、当前激活模型、数据库表、storage/logs 目录和磁盘空间；支持清除检测历史、清除日志、清除非激活模型、一键恢复初始化
- AI 助手：独立“AI深度学习助手”，支持 DeepSeek/OpenAI 兼容问答接口，不影响检测主流程
- 中文前端：Vue3 + Element Plus + ECharts，已统一按钮、输入框、弹窗、抽屉、表格、查询条件区和响应式布局样式

## 技术栈

- 后端：FastAPI、SQLAlchemy、SQLite、JWT、RBAC、Ultralytics YOLOv8、OpenCV、Pillow、Torch
- 前端：Vue3、Vite、TypeScript、Pinia、Vue Router、Axios、Element Plus、ECharts
- 任务：进程内后台队列，支持 `pending/running/paused/cancelled/done/failed`、失败重试、视频异步处理
- 报表与状态：openpyxl、psutil、httpx、nvidia-ml-py
- 依赖文件：后端 `backend/requirements.txt`，前端 `frontend/package.json`

## 目录结构

```text
backend/
  app/
    api/          # 认证、检测、历史、模型、管理、日志、仪表盘、训练分析、系统维护、AI 助手接口
    constants/    # COCO 类别中英文字典
    core/         # YOLO 引擎、推理服务、任务队列、依赖、配置
    db/           # 数据库连接、初始化和轻量 schema patch
    models/       # SQLAlchemy ORM
    schemas/      # Pydantic DTO
    services/     # 业务服务
    utils/         # 文件、图片、视频、时间工具
frontend/
  src/
    api/          # 前后端契约对齐的 API 客户端
    components/   # 可复用组件
    router/       # 路由和权限守卫
    stores/       # 登录态和权限状态
    views/        # 页面
storage/
  uploads/        # 上传文件
  results/        # 检测结果、训练分析 CSV、临时结果、视频帧和检测后视频
  models/         # YOLO 模型文件
```

## 环境要求

- Python：建议使用 Anaconda `ultralytics` 环境
- Node.js：建议 Node.js 18+
- GPU：可选；如需 CUDA 推理，请确保当前 Python 环境中的 PyTorch 与本机 CUDA/显卡驱动匹配
- 默认数据库：SQLite，数据库文件位于后端目录下的 `yolo_web.db`

## 后端依赖

后端依赖文件位于：

```text
backend/requirements.txt
```

当前依赖包括：FastAPI、Uvicorn、SQLAlchemy、Pydantic、JWT/密码加密、Ultralytics、Torch、OpenCV、Pillow、NumPy、openpyxl、psutil、nvidia-ml-py、httpx 等。

在项目推荐的 Anaconda `ultralytics` 环境中安装：

```bash
/e/software/ADeepLearning/Anaconda/envs/ultralytics/python.exe -m pip install -r requirements.txt
```

如果已经进入 `backend` 目录，也可以执行：

```bash
/e/software/ADeepLearning/Anaconda/envs/ultralytics/python.exe -m pip install -r requirements.txt
```

## 后端启动

推荐使用指定的 Anaconda `ultralytics` 环境运行：

```bash
cd E:/DeepLearning/yolo_web/backend
cp .env.example .env
/e/software/ADeepLearning/Anaconda/envs/ultralytics/python.exe -m pip install -r requirements.txt
/e/software/ADeepLearning/Anaconda/envs/ultralytics/python.exe -m uvicorn app.main:app --reload
```

如果已经在 Anaconda Prompt 中激活环境，也可以使用：

```bash
conda activate ultralytics
cd E:/DeepLearning/yolo_web/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

服务地址：

- API：`http://localhost:8000`
- OpenAPI：`http://localhost:8000/docs`
- Health：`http://localhost:8000/health`

默认账号：

```text
admin / admin123456
```

## 前端启动

```bash
cd E:/DeepLearning/yolo_web/frontend
npm install
cp .env.example .env
npm run dev
```

前端地址：

```text
http://localhost:5173
```

生产构建：

```bash
npm --prefix frontend run build
```

## 配置说明

后端 `.env` 主要配置：

```env
APP_NAME=Reusable YOLO Vision Platform
APP_ENV=local
SECRET_KEY=change-this-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./yolo_web.db
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123456
UPLOAD_DIR=../storage/uploads
RESULT_DIR=../storage/results
MODEL_DIR=../storage/models
DEFAULT_MODEL_PATH=
YOLO_DEVICE=auto
CONFIDENCE_THRESHOLD=0.25
IOU_THRESHOLD=0.7
VIDEO_SAMPLE_FPS=2
TASK_MAX_RETRIES=2
STREAM_FRAME_TIMEOUT_SECONDS=30
MAX_UPLOAD_MB=512
AI_ASSISTANT_BASE_URL=
AI_ASSISTANT_API_KEY=
AI_ASSISTANT_MODEL=deepseek-chat
AI_ASSISTANT_TIMEOUT_SECONDS=30
```

AI 助手使用 OpenAI 兼容的 `/chat/completions` 接口。未配置 `AI_ASSISTANT_API_KEY` 时，前端会显示“未配置”，检测主流程不受影响。

## 模型使用

把 YOLOv8 模型文件放到：

```text
storage/models/
```

然后在前端“模型管理”页面登记模型路径，例如：

```text
yolov8n.pt
```

也可以直接上传 `.pt` 模型文件。普通用户可以查看和上传模型；登记路径、激活、修改显示名称、类别映射、切换设备和删除模型需要模型管理权限。激活模型后，后端会通过 `YoloEngine` 热切换当前模型。模型显示名称只影响 UI 展示，不修改模型文件和后端模型名称。

## 类别中英映射

后端内置 YOLOv8 COCO 80 类英文到中文默认字典：

```text
backend/app/constants/coco_classes.py
```

模型管理页会读取模型类别，支持手动维护中文名称。后端数据库字段继续保存英文类别，API 额外返回中文字段：

```json
{
  "class": "person",
  "class_zh": "人",
  "confidence": 0.95,
  "bbox": [0, 0, 100, 100]
}
```

## 检测参数与保存策略

单图、批量和视频接口都支持：

- `confidence`：置信度阈值
- `iou`：IoU 阈值
- `save_history`：是否写入历史记录

`save_history=true` 时，系统写入数据库并保存原图、检测图；视频任务完成后会把检测后视频保存到 `storage/results/videos/`，历史详情优先通过后端 artifact URL 播放本地 mp4，不直接暴露本地磁盘路径。后端支持 HTTP Range，并优先写出 H.264 mp4；旧 FMP4/mp4v 视频在访问时会自动生成 `_browser.mp4` 兼容副本，浏览器仍无法解码时前端会自动切换为检测帧流兜底。

`save_history=false` 时，只保存临时预览文件，不写历史表，适合临时调参。

## 核心接口

### 认证

- `POST /api/auth/login`：登录
- `POST /api/auth/register`：注册普通用户
- `POST /api/auth/reset-password`：按用户名简单重置密码
- `GET /api/auth/me`：当前用户
- `POST /api/auth/logout`：退出

### 检测

- `POST /api/detect/image`：单图检测
- `POST /api/detect/batch`：批量图片检测
- `POST /api/detect/video`：创建视频检测任务，完成后保存检测后本地视频用于历史回放
- `GET /api/detect/tasks/{task_id}`：查询任务状态
- `POST /api/detect/tasks/{task_id}/{pause|resume|cancel|end}`：控制任务
- `GET /api/detect/artifacts/{record_id}?kind=original|result|thumbnail|video`：历史原图、检测图、检测后视频或视频缩略图；mp4 支持 Range 播放
- `GET /api/detect/temp/{name}`：仅本地检测的临时预览文件
- `GET /api/detect/video/stream/{task_id}`：视频 MJPEG 帧流
- `GET /api/detect/realtime/stream`：实时视频流检测

### 历史

- `GET /api/history`：分页查询检测历史，支持来源、英文类别、中文类别、用户筛选
- `GET /api/history/export`：按当前筛选条件导出 Excel
- `GET /api/history/{record_id}`：检测详情
- `DELETE /api/history/{record_id}`：删除检测记录
- `DELETE /api/history/batch/delete`：批量删除

### 训练分析

- `POST /api/training-analysis/upload`：上传 YOLO `results.csv`，写入训练分析记录并返回解析摘要
- `GET /api/training-analysis/files`：列出已上传 CSV 和数据库记录
- `GET /api/training-analysis/summary?name=`：读取指定 CSV 并返回图表数据与关键指标
- `GET /api/training-analysis/export?name=`：导出当前训练分析报告
- `DELETE /api/training-analysis/{name}`：删除当前分析记录和对应 CSV 文件
- `DELETE /api/training-analysis/clear`：清空全部训练分析记录和 CSV 文件
- `POST /api/training-analysis/ai-report`：基于 summary 生成中文 AI 训练分析

### 模型

- `GET /api/models`：模型列表
- `POST /api/models`：登记模型路径，模型名称、路径和版本号不能为空
- `POST /api/models/upload`：上传模型（拥有模型查看权限的用户可用）
- `POST /api/models/{model_id}/activate`：激活模型
- `PATCH /api/models/{model_id}/display-name`：修改显示名称
- `PATCH /api/models/{model_id}/class-mapping`：保存类别中文映射
- `DELETE /api/models/{model_id}`：删除非激活模型
- `GET /api/models/active`：当前模型状态
- `GET /api/models/devices`：可用推理设备
- `POST /api/models/device`：切换当前激活模型设备

### 管理、日志、仪表盘、系统维护、AI 助手

- `GET /api/admin/users?keyword=`：用户查询
- `POST /api/admin/users`：创建用户
- `PUT /api/admin/users/{user_id}`：更新用户状态、角色或重置密码
- `GET /api/admin/roles`：角色列表
- `GET /api/admin/permissions`：权限列表
- `GET /api/logs`：日志列表，支持中文级别/模块/类型查询
- `DELETE /api/logs/{log_id}`：删除单条日志
- `DELETE /api/logs/batch/delete`：批量删除日志
- `DELETE /api/logs/by-date`：按日期范围删除日志
- `GET /api/dashboard/metrics`：统计指标和管理员系统状态
- `GET /api/maintenance/status`：系统维护状态检查，包含 GPU/CUDA/torch、模型、数据库和文件系统
- `DELETE /api/maintenance/history`：清除检测历史数据库记录和检测文件，保留目录结构
- `DELETE /api/maintenance/logs`：清除日志数据库记录和日志文件，保留目录结构
- `DELETE /api/maintenance/models`：清除非激活模型记录和可安全删除的模型文件，保留当前激活模型
- `POST /api/maintenance/restore-initial`：一键恢复初始化，保留 admin、默认配置、系统基础字典和当前激活/默认模型
- `GET /api/assistant/status`：AI 助手配置状态
- `POST /api/assistant/chat`：AI 助手问答

## RBAC 权限码

- `detect:run`：执行检测
- `history:read`：查看历史
- `history:manage`：管理历史
- `model:read`：查看模型
- `model:manage`：管理模型
- `log:read`：查看日志
- `admin:user`：用户与角色管理
- `assistant:use`：使用 AI 助手

## 验证命令

后端编译检查：

```bash
/e/software/ADeepLearning/Anaconda/envs/ultralytics/python.exe -m compileall backend/app
```

前端构建检查：

```bash
npm --prefix frontend run build
```

依赖安装检查：

```bash
/e/software/ADeepLearning/Anaconda/envs/ultralytics/python.exe -m pip install -r requirements.txt
```

## 常见目录和数据

- 上传文件：`storage/uploads/`
- 检测结果：`storage/results/`
- 检测后视频：`storage/results/videos/`
- 视频抽样帧：`storage/results/video_frames/`
- 训练分析 CSV：`storage/results/training_analysis/`
- 模型文件：`storage/models/`
- 后端日志：`backend/logs/`
- SQLite 数据库：`backend/yolo_web.db`

## 生产扩展建议

- SQLite 替换为 PostgreSQL 或 MySQL
- 进程内任务队列替换为 Redis + Celery/RQ
- 本地 `storage/` 替换为对象存储
- YOLO 推理服务可独立部署为 GPU worker
- 为大视频增加并发限制、分片处理和断点续处理
- 使用 Alembic 管理数据库迁移
- 注册和忘记密码接入邮箱、短信或管理员审批流程
