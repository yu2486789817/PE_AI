# AIChat - AI 智能聊天与报告服务

## 模块概述

AIChat 是体育教学平台的 AI 智能助手服务，提供两个核心功能：
1. **AI 聊天助手**：为学生和教师提供个性化的运动指导和教学建议
2. **AI 分析报告**：基于学生运动数据生成智能分析报告

**技术方案**：Ollama + 微调后的 Qwen2.5-3B-PE-Sports 模型

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
│  │                    Ollama 推理服务                               ││
│  │                                                                  ││
│  │   ┌────────────────────────────────────────────────────────┐    ││
│  │   │              qwen2.5-pe-sports                          │    ││
│  │   │         (微调后的体育教学专用模型)                        │    ││
│  │   └────────────────────────────────────────────────────────┘    ││
│  │                                                                  ││
│  │   服务地址: http://localhost:11434                              ││
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

## 目录结构

```
Code/AIChat/
├── chat_module.py          # 聊天核心模块
├── report_module.py        # 报告生成模块
├── database.py             # 数据库模块
├── main.py                 # FastAPI 入口
├── requirements.txt        # Python 依赖
├── .gitignore
├── models/
│   └── qwen2.5-pe-sports.q4_k_m.gguf  # GGUF 量化模型（~2GB）
├── ollama/
│   ├── Modelfile           # Ollama 模型配置
│   └── README.md           # 导入指南
└── finetune/
    ├── dequantize_model.py # 反量化脚本
    └── ...                 # 其他微调脚本
```

## 快速开始

### 1. 安装 Ollama

**Windows:**
访问 https://ollama.com/download 下载 Windows 版本

**Linux/macOS:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. 导入模型到 Ollama

```bash
cd Code/AIChat/ollama
ollama create qwen2.5-pe-sports -f Modelfile
```

### 3. 验证模型

```bash
ollama list
# 应该看到：
# NAME                    ID              SIZE    MODIFIED
# qwen2.5-pe-sports       xxxxx           2.1 GB  x minutes ago

# 测试模型
ollama run qwen2.5-pe-sports "你好"
```

### 4. 启动 AIChat 服务

```bash
conda activate pe_ai
cd Code/AIChat
python main.py
```

服务将在 `http://localhost:5000` 启动。

### 5. 环境变量（可选）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OLLAMA_BASE_URL` | http://localhost:11434 | Ollama 服务地址 |
| `OLLAMA_MODEL` | qwen2.5-pe-sports | Ollama 模型名称 |
| `YOLO_BASE_URL` | http://localhost:8000 | Yolo_backend 服务地址 |
| `MAX_TOKENS` | 512 | 最大生成 token 数 |
| `TEMPERATURE` | 0.9 | 生成温度 |

## 模型说明

### 微调模型特点

| 场景 | 能力 |
|------|------|
| 学生教练 | 动作纠正、训练建议、运动知识科普 |
| 教师助理 | 班级分析、教学方案设计、学生评估 |
| 报告生成 | 运动数据解读、个性化建议生成 |

### 模型文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `models/qwen2.5-pe-sports.q4_k_m.gguf` | ~2GB | GGUF 量化模型，用于导入 Ollama |
| Ollama 内部存储 | ~2GB | 推理时实际使用（由 Ollama 管理） |

## 核心组件

### 1. chat_module.py - 聊天核心模块

**OllamaLLM 类：**
- 通过 HTTP API 调用 Ollama 服务
- 自动服务状态检查

**ChatManager 类：**
- 会话生命周期管理
- 对话历史持久化

### 2. report_module.py - 报告生成模块

| 类型 | 说明 |
|------|------|
| homework_feedback | 作业反馈分析 |
| personalized_tips | 个性化训练建议 |

### 3. database.py - 数据库模块

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
  "role": "student"
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

## 与 Yolo_backend 数据交互

AIChat 从 Yolo_backend 获取学生运动数据：

```
GET http://localhost:8000/api/student/all-records/{student_id}
```

## 错误码

| HTTP 状态码 | 错误信息 | 说明 |
|------------|---------|------|
| 200 | - | 成功 |
| 400 | 用户ID不能为空 | 缺少 user_id |
| 404 | 会话不存在 | session_id 无效 |
| 500 | Ollama 服务不可用 | Ollama 未启动或模型未加载 |

## Ollama 常用命令

```bash
ollama list                      # 查看已安装的模型
ollama run qwen2.5-pe-sports     # 运行模型
ollama show qwen2.5-pe-sports    # 查看模型信息
ollama rm qwen2.5-pe-sports      # 删除模型
```

## 注意事项

1. **Ollama 服务**：确保 Ollama 服务在 11434 端口运行
2. **模型导入**：首次使用需要将微调模型导入 Ollama
3. **并发处理**：Ollama 内置请求队列，支持并发
4. **显存管理**：Ollama 自动管理 GPU 显存

## 依赖说明

核心依赖：
- `fastapi` - Web 框架
- `requests` - HTTP 客户端
- `uvicorn` - ASGI 服务器
