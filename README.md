# 工业级可复用 YOLO 视觉检测 Web 系统模板

这是一个中文化、通用化的 YOLOv8 目标检测 Web 系统模板，面向任意目标检测任务。系统不绑定车辆、鱼类、工业缺陷等具体业务，不写死类别，替换模型即可复用到新项目。

## 功能特性

- YOLOv8 工程化封装：单例加载、GPU/CPU 自动切换、模型热切换、线程安全推理
- 检测入口：单张图片、批量图片、视频异步任务
- 权限系统：JWT 登录、用户、角色、权限码、RBAC 路由守卫
- 数据管理：检测记录与检测结果拆表存储，支持历史查询和删除
- 模型管理：上传模型、登记模型路径、激活模型、查看推理设备
- 日志中心：记录登录、检测、模型切换和任务事件
- Dashboard：总检测数、图片/视频数量、活跃用户、7 日趋势、高频类别
- AI 分析：基于真实检测结果 JSON 做统计总结、类别分布和异常提示
- 中文前端：Vue3 + Element Plus + ECharts，工业风检测中台布局

## 技术栈

- 后端：FastAPI、SQLAlchemy、SQLite、JWT、RBAC、Ultralytics YOLOv8、OpenCV
- 前端：Vue3、Vite、TypeScript、Pinia、Vue Router、Axios、Element Plus、ECharts
- 任务：进程内后台队列，支持 `pending/running/done/failed`、失败重试、视频异步处理

## 目录结构

```text
backend/
  app/
    api/          # 认证、检测、历史、模型、管理、日志、仪表盘接口
    core/         # YOLO 引擎、推理服务、任务队列、依赖、配置
    db/           # 数据库连接和初始化
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
  results/        # 检测结果和视频帧
  models/         # YOLO 模型文件
```

## 后端启动

当前项目建议使用你的 Anaconda `ultralytics` 环境：

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

前端地址：`http://localhost:5173`

## 模型使用

把 YOLOv8 模型文件放到：

```text
storage/models/
```

然后在前端“模型管理”页面登记模型路径，例如：

```text
yolov8n.pt
```

也可以直接上传 `.pt` 模型文件。激活模型后，后端会通过 `YoloEngine` 热切换当前模型。

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

### 认证

- `POST /api/auth/login`：登录
- `GET /api/auth/me`：当前用户
- `POST /api/auth/logout`：退出

### 检测

- `POST /api/detect/image`：单图检测
- `POST /api/detect/batch`：批量图片检测
- `POST /api/detect/video`：创建视频检测任务
- `GET /api/detect/tasks/{task_id}`：查询任务状态
- `GET /api/detect/video/stream/{task_id}`：MJPEG 帧流

### 历史

- `GET /api/history`：分页查询检测历史
- `GET /api/history/{record_id}`：检测详情
- `DELETE /api/history/{record_id}`：删除检测记录
- `DELETE /api/history/batch/delete`：批量删除

### 模型

- `GET /api/models`：模型列表
- `POST /api/models`：登记模型路径
- `POST /api/models/upload`：上传模型
- `POST /api/models/{model_id}/activate`：激活模型
- `GET /api/models/active`：当前模型状态

### 管理、日志、仪表盘

- `GET /api/admin/users`
- `POST /api/admin/users`
- `GET /api/admin/roles`
- `GET /api/admin/permissions`
- `GET /api/logs`
- `GET /api/dashboard/metrics`

## RBAC 权限码

- `detect:run`：执行检测
- `history:read`：查看历史
- `history:manage`：管理历史
- `model:read`：查看模型
- `model:manage`：管理模型
- `log:read`：查看日志
- `admin:user`：用户与角色管理

## 生产扩展建议

- SQLite 替换为 PostgreSQL 或 MySQL
- 进程内任务队列替换为 Redis + Celery/RQ
- 本地 `storage/` 替换为对象存储
- YOLO 推理服务可独立部署为 GPU worker
- 为大视频增加大小限制、并发限制、任务取消和断点续处理
- 使用 Alembic 管理数据库迁移
