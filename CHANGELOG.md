# YOLO Web — 版本更新日志

## 🧪 视觉实验工作站 (Workstation) 系列

### v3 — UI 深化打磨 (2026-05-10)

**登录 / 认证体验全面升级**
- 全新深色科技分屏布局：左侧 Hero 区搭载动态网格背景与扫描线动效，右侧玻璃态表单
- 浮动检测框脉冲动画与漂移效果，营造 AI 视觉实验室氛围
- 登录、注册、忘记密码页面统一交互风格

**Dashboard 仪表盘增强**
- Hero 横幅光晕装饰与胶囊标签样式
- 指标卡片顶部渐变色带，"悬浮即展现"交互反馈
- 系统资源区边框过渡动效

**各视图体验提升**
- AssistantView 对话界面排版优化
- DetectHomeView 检测入口卡片与布局微调
- LogsView 日志页信息层次增强
- MaintenanceView 运维页视觉一致性提升
- TrainingAnalysisView 训练分析视图大幅增强，更丰富的数据展示
- UserAdminView 用户管理页面样式精化

---

### v2 — UI 对齐与排版一致性

- 提取共享样式变量与 Mixin，消除跨视图重复 CSS
- 标准化组件间距、圆角、阴影层级
- 统一动画缓动曲线与过渡时长
- 修复多个视图中文案截断与错位问题

---

### v1 — 深色主题前端全面重写

- 全新深色主题视觉系统，CSS 自定义属性驱动
- 完整重构 10+ 视图页面（Dashboard、检测、日志、运维、训练分析等）
- 新增通用组件：AnimatedNumber、ProgressRing、StatusPulse、MotionPanel 等
- 检测功能组件化：BatchPipeline、DetectionCanvas、DetectionResultInspector、RealtimeEventFeed
- 响应式布局适配移动端与宽屏工作站
- AppLayout 导航与侧栏重构
