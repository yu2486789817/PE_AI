# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**重要：请始终使用中文进行思考和回复。**

## 项目概述

PE AI Manager（大学体育智能课堂平台）是一个面向高校体育教学的智能化管理系统，利用 AI 视觉分析技术（YOLO）实现体育动作的自动评估。系统支持三种用户角色：学生、教师和管理员。

**核心 AI 功能：**
1. **YOLO 视频识别**：基于 YOLOv8-pose 的健身动作识别与计数
2. **本地 LLM 微调**：基于 LoRA 的体育教学领域模型微调与部署

## 系统架构

项目采用微服务架构，包含以下主要组件：

```
Code/
├── PE-AI-Backend/          # Spring Boot 3.x 后端服务 (端口 5001)
├── PE_AI_Manager_Frontend/ # Vue 3 + Vite 教师/管理员 Web 前端
├── PE_AI_Student_UniApp/   # Uni-app 学生移动端应用
├── Yolo_backend/           # Python FastAPI AI 视频处理服务 (端口 8000)
├── AIChat/                 # Python FastAPI AI 聊天助手服务 (端口 5000)
└── sql/                    # 数据库脚本
```

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              整体架构                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        前端层                                        │   │
│  │  ┌───────────────────┐  ┌───────────────────┐                      │   │
│  │  │ PE_AI_Manager_    │  │ PE_AI_Student_    │                      │   │
│  │  │ Frontend (Vue 3)  │  │ UniApp (Uni-app)  │                      │   │
│  │  │ 教师/管理员端      │  │ 学生移动端         │                      │   │
│  │  └───────────────────┘  └───────────────────┘                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     业务后端层 (Spring Boot 3.x)                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    PE-AI-Backend (端口 5001)                 │   │   │
│  │  │  • 用户认证与授权 (JWT)                                      │   │   │
│  │  │  • 课程管理                                                  │   │   │
│  │  │  • 作业管理                                                  │   │   │
│  │  │  • 提交管理                                                  │   │   │
│  │  │  • AI 服务代理                                               │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│          ┌─────────────────────────┼─────────────────────────┐             │
│          ▼                         ▼                         ▼             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   MySQL 数据库   │    │  Yolo_backend   │    │    AIChat       │        │
│  │   (业务数据)     │    │  (端口 8000)    │    │  (端口 5000)    │        │
│  │                 │    │                 │    │                 │        │
│  │  • 用户信息      │    │  • 视频处理     │    │  • AI 聊天      │        │
│  │  • 课程信息      │    │  • 动作识别     │    │  • 报告生成     │        │
│  │  • 作业信息      │    │  • 结果存储     │    │  • 本地 LLM     │        │
│  │  • 提交记录      │    │  (SQLite)       │    │  (SQLite)       │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 服务依赖关系

- **Backend** (5001) → MySQL 数据库，调用 Yolo_backend (8000) 和 AIChat (5000)
- **Yolo_backend** (8000) → YOLOv8-pose 模型，SQLite 存储运动记录
- **AIChat** (5000) → 本地部署的微调 LLM（Qwen2.5-7B + LoRA），SQLite 存储聊天会话
- **AIChat** (5000) → 调用 Yolo_backend (8000) 获取学生运动数据用于生成报告

## 开发命令

### 后端服务 (Spring Boot)
```bash
cd Code/PE-AI-Backend
mvn spring-boot:run                    # 启动开发服务器
mvn test                               # 运行测试
mvn clean package -DskipTests          # 打包构建
```

### Web 前端 (Vue 3)
```bash
cd Code/PE_AI_Manager_Frontend
npm install                            # 安装依赖
npm run dev                            # 启动开发服务器
npm run build                          # 生产环境构建
npm run lint                           # 运行 ESLint 检查
```

### 学生移动端 (Uni-app)
```bash
cd Code/PE_AI_Student_UniApp
npm install
npm run dev:h5                         # H5 开发模式
npm run build:h5                       # H5 生产构建
npm run dev:mp-weixin                  # 微信小程序开发模式
npm run build:mp-weixin                # 微信小程序构建（产物在 dist/build/mp-weixin，用微信开发者工具导入）
```

> 注意：小程序播放 Supabase 视频直链，需在微信公众平台把确切域名（如 `yonuszotqcyqphhxrqaq.supabase.co`）加入 downloadFile 合法域名。

### AI 服务 (Python)

#### YOLO 视频处理服务
```bash
cd Code/Yolo_backend
pip install ultralytics fastapi uvicorn opencv-python numpy
python main.py                         # 启动服务 (端口 8000)
```

#### AI 聊天助手服务（本地 LLM）
```bash
cd Code/AIChat

# 1. 下载基础模型（首次运行）
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2.5-7B-Instruct', cache_dir='./models')"

# 2. 启动 vLLM 推理服务
python -m vllm.entrypoints.openai.api_server --model ./models/Qwen2.5-7B-Instruct --port 8001

# 3. 启动 FastAPI 服务
python main.py                         # 启动服务 (端口 5000)
```

## 数据库配置

### MySQL 数据库 (se_project)

1. 创建 MySQL 数据库 `se_project`
2. 执行 `Code/sql/` 目录下的 SQL 脚本创建表结构
3. 在 `Code/PE-AI-Backend/src/main/resources/application.yml` 中配置数据库连接

**主要数据表：**

| 表名 | 说明 | 关键字段 |
|-----|------|---------|
| student | 学生用户 | id, name, email, password |
| teacher | 教师用户 | id, name, email, password |
| std_student | 学生基准表 | id (用于注册验证) |
| std_teacher | 教师基准表 | id (用于注册验证) |
| course | 课程 | id (课号/主键), teacher_id, name, code (6位课程码/邀请码), semester |
| homework | 作业 | id, course_id, title, deadline |
| submit | 提交 | id, homework_id, student_id, video_url, score, ai_feedback |
| ai_type | 作业AI类型 | homework_id, type, num |
| student_course | 学生课程关系 | student_id, course_id |

### SQLite 数据库

**Yolo_backend (exercise_feedback.db)：**

| 表名 | 说明 | 关键字段 |
|-----|------|---------|
| exercise_feedback | 运动反馈记录 | id, homework_id, student_id, pose_type, total_count, correct_count, feedback_json |

**AIChat (ai_chat.db)：**

| 表名 | 说明 | 关键字段 |
|-----|------|---------|
| sessions | 聊天会话 | id, user_id, title, model, role |
| messages | 聊天消息 | id, session_id, role, content |
| ai_analysis_reports | AI分析报告 | id, homework_id, student_id, analysis_type, report_content |

### 数据库关联关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          数据库关联设计                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MySQL 数据库 (se_project)                SQLite 数据库                     │
│  ┌─────────────────────┐                 ┌─────────────────────┐           │
│  │ student             │                 │ sessions (AIChat)   │           │
│  │ ─────────────────── │                 │ ─────────────────── │           │
│  │ id (PK)             │◄────────────────│ user_id             │           │
│  └─────────────────────┘                 └─────────────────────┘           │
│                                                                          │
│  ┌─────────────────────┐                 ┌─────────────────────┐           │
│  │ homework            │                 │ exercise_feedback   │           │
│  │ ─────────────────── │                 │ (Yolo_backend)      │           │
│  │ id (PK)             │◄────────────────│ homework_id         │           │
│  └─────────────────────┘                 │ student_id          │──┐        │
│                                          └─────────────────────┘  │        │
│  ┌─────────────────────┐                           │                │        │
│  │ submit              │                           │                │        │
│  │ ─────────────────── │                           │                │        │
│  │ homework_id (FK)    │───────────────────────────┘                │        │
│  │ student_id (FK)     │────────────────────────────────────────────┘        │
│  │ ai_feedback         │  ← 可存储 AI 反馈摘要                             │
│  └─────────────────────┘                                                    │
│                                                                             │
│  ┌─────────────────────┐                 ┌─────────────────────┐           │
│  │ homework            │                 │ ai_analysis_reports │           │
│  │ ─────────────────── │                 │ (AIChat)            │           │
│  │ id (PK)             │◄────────────────│ homework_id         │           │
│  └─────────────────────┘                 │ student_id          │           │
│                                          │ report_content      │           │
│                                          └─────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## AI 模块详细说明

### Yolo_backend - 视频动作识别

**架构文档**：详见 [Code/Yolo_backend/README.md](Code/Yolo_backend/README.md)

**核心组件：**
- `AIGym`：核心识别类，协调 YOLO 模型和运动跟踪器
- `PushupTracker`、`SquatTracker`、`DeadliftTracker`：各运动的识别逻辑

**支持的动作类型：**
| 动作 | 英文标识 | 关键点 |
|-----|---------|-------|
| 俯卧撑 | pushup | 右肩-右肘-右腕 |
| 深蹲 | squat | 右髋-右膝-右踝 |
| 硬拉 | deadlift | 右肩-右髋-右膝 |

**扩展新运动：**
1. 创建新的 Tracker 类（参考 `pushup.py`）
2. 在 `ai_gym.py` 中注册
3. 在 `main.py` 的 `supported_poses` 中添加

### AIChat - 本地 LLM 微调与部署

**架构文档**：详见 [Code/AIChat/README.md](Code/AIChat/README.md)

**技术栈：**
- 基础模型：Qwen2.5-7B-Instruct
- 微调方法：LoRA (Low-Rank Adaptation)
- 推理框架：vLLM（高性能）或 Transformers

**LoRA 微调流程：**
1. 下载基础模型（ModelScope 或 HuggingFace）
2. 准备训练数据（体育教学领域问答）
3. 运行微调脚本
4. 合并模型并导出
5. 部署推理服务

**训练数据规划：**
```
体育教学领域数据/
├── 学生教练场景/    # 动作纠正、训练计划、运动知识
├── 教师助理场景/    # 班级分析、教学方案、学生评估
└── 通用体育知识/    # 运动营养、伤病预防、训练方法
```

**关键配置文件：**
- `chat_module.py`：会话管理和 LLM 调用
- `report_module.py`：AI 分析报告生成

## 关键技术细节

### 用户认证
- 自定义 JWT 实现，位于 `SecurityUtil.java`
- 前端将 token 存储在 localStorage
- `router/index.js` 中的路由守卫实现基于角色的访问控制

### 用户注册流程
- 用户必须先存在于基准表（`std_student`/`std_teacher`）中才能注册
- 注册时会验证用户 ID 是否在基准表中存在

### 课程码与选课
- 老师建课时后端生成 **6 位大写字母+数字**的课程码（`LegacyCourseController.newCourse`，字符集排除易混的 I/O/0/1，含唯一性校验）
- 学生通过课程码加入课程；前端输入校验为 `/^[A-Z0-9]{6}$/` 并做大写归一化
- 课程主键 `id` 即「课号」，与「课程码/邀请码」`code` 是两个不同字段，勿混用

### 视频存储（Supabase Storage）
- 教学视频（`/Teaching-video/upload`）和学生作业原始视频（`/Homework/upload_submit`）持久化到 **Supabase Storage**，由 `SupabaseStorageService` 统一处理
- 通过环境变量 `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` / `SUPABASE_BUCKET` 配置；未配置时回退到本地磁盘（仅适合本地开发）
- 旧的 `/Teaching-video/files/{filename}` 链接在云模式下 302 重定向到 Supabase 公共 URL
- 部署细节见 [DEPLOY_RENDER_SUPABASE.md](DEPLOY_RENDER_SUPABASE.md)

### AI 视频处理
- 使用 YOLOv8-pose 模型进行人体关键点检测
- 通过 SSE 流式传输实现逐帧实时反馈
- 处理结果存储在 SQLite 数据库 (`exercise_feedback.db`)

### 前后端通信
- RESTful API，使用 `Result<T>` 统一响应格式
- 配置 CORS 支持跨域请求
- 后端作为 AI 服务的代理（配置在 `application.yml`）

### 遗留接口数据格式（重要）
- 一批遗留接口（`LegacyCourseController`、`LegacyUserController`，路径如 `/Course/*`、`/Homework/*`、`/Class/*`、`/User/*`）返回的是**以 `\t\r` 分隔、按固定位置拼接**的字符串，空字段也占位（如 `教师id\t\r课程名\t\r描述\t\r课程码\t\r学期\t\r状态\t\r时间`）。
- 列表型接口在无数据时返回字符串 `"NULL"`（不是空、不是 null）。
- **课号(课程号)不在返回串里**——它就是课程主键 `id`，作为查询入参传入。
- 前端解析必须用共享工具 `PE_AI_Manager_Frontend/src/utils/legacyParse.js`，禁止各页面手写解析：
  - `splitLegacyRecord(raw)`：拆分记录、保留空字段占位（**不可 `filter` 空值，否则字段左移错位**）
  - `parseLegacyIdList(raw)`：解析 ID 列表，排除空值与 `"NULL"` 哨兵
  - `parseCourseInfo(raw, courseId)` / `parseHomeworkInfo(raw, id)`：返回标准字段对象
- 解析器保持纯函数、无业务 flag；各页面的差异（改名、转布尔、补充字段、文案）留在调用点。

## API 结构

### 后端接口 (PE-AI-Backend:5001)

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/api/user/*` | - | 用户认证和管理 |
| `/api/course/*` | - | 课程增删改查 |
| `/api/homework/*` | - | 作业管理 |
| `/api/submit/*` | - | 作业提交 |

### YOLO 服务接口 (Yolo_backend:8000)

详见 [Code/Yolo_backend/README.md](Code/Yolo_backend/README.md)

| 接口 | 方法 | 说明 | 调用方 |
|-----|------|------|-------|
| `/health` | GET | 健康检查 | Backend |
| `/supported_poses` | GET | 支持的动作类型 | 前端 |
| `/stream_process_video` | POST | 实时视频处理（SSE 流式） | 前端 |
| `/process_and_save_video` | POST | 处理并保存视频 | 前端/Backend |
| `/get_processed_video` | GET | 获取处理后的视频 | 前端 |
| `/query_records` | GET | 查询运动反馈记录 | 前端/Backend |
| `/api/student/all-records/{student_id}` | GET | 获取学生所有记录 | AIChat |

### AI 聊天接口 (AIChat:5000)

详见 [Code/AIChat/README.md](Code/AIChat/README.md)

| 接口 | 方法 | 说明 | 调用方 |
|-----|------|------|-------|
| `/api/sessions` | POST | 创建会话 | 前端 |
| `/api/sessions` | GET | 获取用户所有会话 | 前端 |
| `/api/sessions/{id}` | GET | 获取会话详情 | 前端 |
| `/api/sessions/{id}/messages` | POST | 发送消息 | 前端 |
| `/api/sessions/{id}` | DELETE | 删除会话 | 前端 |
| `/api/analysis/generate` | POST | 生成 AI 分析报告 | 前端 |
| `/api/analysis/query` | GET | 查询报告 | 前端 |

### 服务间通信

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          服务间通信流程                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 视频处理流程                                                             │
│     前端 ──POST /process_and_save_video──▶ Yolo_backend (SSE 流式响应)      │
│     Yolo_backend ──INSERT──▶ exercise_feedback.db (SQLite)                 │
│                                                                             │
│  2. AI 聊天流程                                                              │
│     前端 ──POST /api/sessions/{id}/messages──▶ AIChat                       │
│     AIChat ──本地推理──▶ Qwen2.5-7B-PE-Sports                              │
│     AIChat ──INSERT──▶ ai_chat.db (SQLite)                                 │
│                                                                             │
│  3. 报告生成流程                                                             │
│     前端 ──POST /api/analysis/generate──▶ AIChat                            │
│     AIChat ──GET /api/student/all-records──▶ Yolo_backend                  │
│     AIChat ──本地推理──▶ Qwen2.5-7B-PE-Sports                              │
│     AIChat ──INSERT──▶ ai_chat.db (SQLite)                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 部署架构

- **Web 前端**：部署在 **Vercel**（连接 git，push 到 master 自动部署）
- **后端**：部署在 **Render**（Docker，免费档，连接 git 自动部署；免费档闲置会休眠，首次请求冷启动较慢）
- **数据库**：生产用 **Supabase PostgreSQL**（本地开发用 MySQL）
- **视频文件**：**Supabase Storage**（见上文「视频存储」）
- **AI 服务**（Yolo_backend / AIChat）：按需部署，后端通过 `YOLO_BASE_URL` / `AICHAT_BASE_URL` 环境变量指向其地址
- 本地 `npm run dev` 通过 `vite.config.js` 代理把 API 请求转发到 Render 后端，即本地前端 + 线上后端/数据库

## 开发注意事项

1. **遵循 `karpathy-guidelines.SKILL.md`**：最小化改动、不臆造兼容代码、显式处理哨兵值与位置契约、删除自身改动产生的死代码
2. **遗留接口解析统一走 `legacyParse.js`**（见「遗留接口数据格式」），勿在页面里手写 `\t\r` 拆分
3. **本地 LLM 部署**：项目已从 API Key 调用方式转变为本地部署 + LoRA 微调
4. **模型下载**：推荐使用 ModelScope（国内速度更快）
5. **显存要求**：7B 模型推理需要至少 16GB 显存，微调需要更多
6. **数据质量**：训练数据需要人工审核，确保准确性
