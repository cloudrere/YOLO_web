# 工业级可复用 YOLO 视觉检测 Web 系统模板

这是一个通用目标检测 Web 系统模板，面向任意 YOLOv8 目标检测任务。系统不绑定任何业务场景，不写死类别，替换模型即可复用到新项目。

## 技术栈

- 后端：FastAPI、SQLAlchemy、SQLite、JWT、RBAC、Ultralytics YOLOv8、OpenCV
- 前端：Vue3、Vite、TypeScript、Pinia、Vue Router、Axios、Element Plus、ECharts
- 推理：线程安全 YOLO 单例、GPU/CPU 自动切换、动态模型热切换、图片/批量/视频处理
- 任务：进程内后台队列，支持 `pending/running/done/failed`、失败重试、视频异步处理

## 目录结构

```text
backend/
  app/
    api/          # auth, detect, history, model, admin, log, dashboard
    core/         # yolo_engine, inference_service, task_queue, deps, config
    db/           # SQLAlchemy session and init
    models/       # ORM models
    schemas/      # Pydantic DTO
    services/     # business services
    utils/         # file/image/video/time helpers
frontend/
  src/
    api/          # aligned API clients and TypeScript contracts
    components/   # reusable UI components
    router/       # route guards
    stores/       # auth and permissions
    views/        # pages
storage/
  uploads/
  results/
  models/
```

## 后端启动

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

- 用户名：`admin`
- 密码：`admin123456`

## 前端启动

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

前端地址：`http://localhost:5173`

## 模型使用

把 YOLOv8 模型文件放到：

```text
storage/models/
```

然后在前端 Models 页面登记模型路径，例如：

```text
yolov8n.pt
```

也可以直接上传 `.pt` 模型文件。激活模型后，后端会通过 `YoloEngine` 热切换模型。

## 统一 API 响应契约

所有业务接口返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

检测结果严格返回：

```json
{
  "class": "string",
  "confidence": 0.95,
  "bbox": [0, 0, 100, 100]
}
```

内部数据库字段使用 `class_name`，API 输出转换为 `class`，避免 Python 保留字冲突。

## 核心接口

### Auth

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`

### Detect

- `POST /api/detect/image`
- `POST /api/detect/batch`
- `POST /api/detect/video`
- `GET /api/detect/tasks/{task_id}`
- `GET /api/detect/video/stream/{task_id}`

### History

- `GET /api/history`
- `GET /api/history/{record_id}`
- `DELETE /api/history/{record_id}`
- `DELETE /api/history/batch/delete`

### Model

- `GET /api/models`
- `POST /api/models`
- `POST /api/models/upload`
- `POST /api/models/{model_id}/activate`
- `GET /api/models/active`

### Admin / Logs / Dashboard

- `GET /api/admin/users`
- `POST /api/admin/users`
- `GET /api/admin/roles`
- `GET /api/admin/permissions`
- `GET /api/logs`
- `GET /api/dashboard/metrics`

## RBAC 权限码

- `detect:run`
- `history:read`
- `history:manage`
- `model:read`
- `model:manage`
- `log:read`
- `admin:user`

## YOLO 工程化特性

`backend/app/core/yolo_engine.py` 提供：

- 单例加载，避免重复加载模型
- `cuda:0` / `cpu` 自动选择
- `threading.RLock` 保护模型加载、切换、推理
- 动态模型切换，失败时不破坏旧模型
- 单图推理、批量推理、视频帧推理
- 类别名来自模型 `names`，不写死任何类别

`backend/app/core/inference_service.py` 提供：

- 上传文件保存
- 推理统一入口
- 检测记录和结果拆表落库
- 视频异步任务
- MJPEG 帧流输出
- 基于真实检测结果 JSON 的统计分析

## AI 分析模块

AI 分析不调用外部大模型，也不生成业务推断，只基于真实检测结果 JSON 统计：

- 总目标数和类别数
- 类别分布、平均置信度、占比
- 低置信度提示
- 类别集中提示
- bbox 面积异常提示

## Dashboard 指标

- `total_detections`
- `image_count`
- `video_count`
- `active_users`
- `daily_trend_7d`
- `top_detected_classes`

## 生产扩展建议

- SQLite 替换为 PostgreSQL 或 MySQL
- 进程内任务队列替换为 Redis + Celery/RQ
- 本地 `storage/` 替换为对象存储
- YOLO 推理服务可独立部署为 GPU worker
- 为大视频增加大小限制、并发限制、任务取消和断点续处理
- 使用 Alembic 管理数据库迁移
