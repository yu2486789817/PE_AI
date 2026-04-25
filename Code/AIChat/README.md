# AIChat - AI 智能聊天与报告服务

## 模块概述

AIChat 是体育教学平台的 AI 智能助手服务，提供两个核心功能：
1. **AI 聊天助手**：为学生和教师提供个性化的运动指导和教学建议
2. **AI 分析报告**：基于学生运动数据生成智能分析报告

**技术方案**：本地部署 Qwen2.5-7B-Instruct + LoRA 微调（体育教学领域）

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AIChat 架构                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────────────────────────────────────┐│
│  │   FastAPI   │    │              核心服务层                      ││
│  │   API 层    │───▶│  ┌─────────────┐  ┌─────────────────────┐  ││
│  │   (5000)    │    │  │ ChatManager │  │  ReportGenerator    │  ││
│  └─────────────┘    │  │  会话管理   │  │    报告生成         │  ││
│                     │  └─────────────┘  └─────────────────────┘  ││
│                     └─────────────────────────────────────────────┘│
│                                │                                    │
│                                ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    本地 LLM 推理层                               ││
│  │                                                                  ││
│  │   ┌────────────────────────────────────────────────────────┐    ││
│  │   │              Qwen2.5-7B-PE-Sports                        │    ││
│  │   │         (微调后的体育教学专用模型)                        │    ││
│  │   │                                                          │    ││
│  │   │   Base: Qwen2.5-7B-Instruct                              │    ││
│  │   │   + LoRA Adapter (体育教学领域微调)                       │    ││
│  │   └────────────────────────────────────────────────────────┘    ││
│  │                                                                  ││
│  │   推理后端: Transformers (4-bit 量化)                           ││
│  │   显存占用: ~5GB                                                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                │                                    │
│                                ▼                                    │
│  ┌─────────────┐              ┌─────────────┐                       │
│  │   SQLite    │              │  Yolo_backend│                       │
│  │   数据库    │◀────────────▶│  (数据源)   │                       │
│  └─────────────┘              └─────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 环境准备

```bash
# 激活 conda 环境
conda activate pe_ai

# 进入 AIChat 目录
cd Code/AIChat
```

### 2. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:5000` 启动。

### 3. 环境变量（可选）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MODEL_PATH` | 自动检测 | 模型路径（优先使用微调模型） |
| `YOLO_BASE_URL` | http://localhost:8000 | Yolo_backend 服务地址 |
| `LOAD_IN_4BIT` | true | 推理时使用 4-bit 量化 |
| `LOAD_IN_8BIT` | false | 推理时使用 8-bit 量化 |
| `MAX_TOKENS` | 2048 | 最大生成 token 数 |
| `TEMPERATURE` | 0.7 | 生成温度 |

## 模型说明

### 模型自动选择

服务启动时会自动检测并选择模型：

1. **优先**：`./models/Qwen2.5-7B-PE-Sports`（微调后的模型）
2. **回退**：`./models/Qwen/Qwen2___5-7B-Instruct`（基础模型）

### 微调模型特点

微调后的模型针对体育教学场景优化：

| 场景 | 能力 |
|------|------|
| 学生教练 | 动作纠正、训练建议、运动知识科普 |
| 教师助理 | 班级分析、教学方案设计、学生评估 |
| 报告生成 | 运动数据解读、个性化建议生成 |

## 核心组件

### 1. chat_module.py - 聊天核心模块

**LocalLLM 类：**
- 本地模型加载与推理
- 支持 4-bit/8-bit 量化
- ChatML 提示词格式

**ChatManager 类：**
- 会话生命周期管理
- 对话历史持久化
- 系统提示词管理

### 2. report_module.py - 报告生成模块

**报告类型：**
| 类型 | 说明 |
|------|------|
| homework_feedback | 作业反馈分析 |
| personalized_tips | 个性化训练建议 |

### 3. database.py - 数据库模块

**SQLite 表结构：**
- `sessions` - 会话记录
- `messages` - 消息历史
- `ai_analysis_reports` - 分析报告

## API 接口

### 聊天接口

#### 创建会话
```
POST /api/sessions
Content-Type: application/json

{
  "user_id": "student001",
  "role": "student"  // student 或 teacher
}
```

#### 发送消息
```
POST /api/sessions/{session_id}/messages
Content-Type: application/json

{
  "message": "我的俯卧撑正确率不高，怎么改进？"
}
```

#### 获取会话列表
```
GET /api/sessions?user_id=student001
```

#### 删除会话
```
DELETE /api/sessions/{session_id}
```

### 报告接口

#### 生成分析报告
```
POST /api/analysis/generate
Content-Type: application/json

{
  "student_id": "student001",
  "analysis_type": "homework_feedback",
  "homework_id": "hw001"
}
```

#### 查询报告
```
GET /api/analysis/query?student_id=student001
```

## 数据库设计

### sessions 表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| user_id | TEXT | 用户ID |
| title | TEXT | 会话标题 |
| model | TEXT | 使用的模型 |
| role | TEXT | 用户角色 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### messages 表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| session_id | INTEGER | 会话ID |
| role | TEXT | 角色 |
| content | TEXT | 消息内容 |
| timestamp | TIMESTAMP | 时间戳 |

### ai_analysis_reports 表

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| homework_id | TEXT | 作业ID |
| student_id | TEXT | 学生ID |
| analysis_type | TEXT | 分析类型 |
| report_content | TEXT | 报告内容 |
| raw_data | TEXT | 原始数据 |
| created_at | TIMESTAMP | 创建时间 |

## 与 Yolo_backend 数据交互

AIChat 从 Yolo_backend 获取学生运动数据：

```
GET http://localhost:8000/api/student/all-records/{student_id}
```

**数据流程：**
1. 接收报告生成请求
2. 从 Yolo_backend 获取运动数据
3. 构建提示词（System Prompt + 运动数据）
4. 调用本地 LLM 生成报告
5. 保存报告到 SQLite
6. 返回结果

## 错误码

| HTTP 状态码 | 错误信息 | 说明 |
|------------|---------|------|
| 200 | - | 成功 |
| 400 | 用户ID不能为空 | 缺少 user_id |
| 404 | 会话不存在 | session_id 无效 |
| 500 | 模型加载失败 | LLM 加载异常 |

## 微调指南

详细的微调流程请参考 [finetune/README.md](finetune/README.md)。

### 微调流程概览

```
1. 下载基础模型 → python finetune/download_model.py
2. 生成训练数据 → python finetune/generate_training_data.py
3. 运行 LoRA 微调 → python finetune/finetune_lora.py
4. 合并 LoRA 权重 → python finetune/merge_lora.py
5. 重启服务 → python main.py（自动使用微调模型）
```

## 注意事项

1. **显存需求**：4-bit 量化推理约需 5GB 显存
2. **首次启动**：模型加载需要 30-60 秒
3. **并发处理**：建议使用队列处理并发请求
4. **模型版本**：推荐 Qwen2.5 系列，中文能力强

## 依赖说明

详见 [requirements.txt](requirements.txt)

核心依赖：
- `transformers` - 模型加载与推理
- `peft` - LoRA 适配器支持
- `bitsandbytes` - 量化支持
- `fastapi` - Web 框架
- `modelscope` - 模型下载
