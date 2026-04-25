# AI 服务启动指南

本文档说明如何启动 Yolo_backend 和 AIChat 两个 AI 服务。

## 目录

- [环境要求](#环境要求)
- [快速启动](#快速启动)
- [模型下载](#模型下载)
- [微调训练](#微调训练)
- [常见问题](#常见问题)

---

## 环境要求

### 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|-----|---------|---------|
| CPU | 4核 | 8核以上 |
| 内存 | 8GB | 16GB以上 |
| GPU | 无（CPU推理） | NVIDIA GPU，6GB显存以上 |
| 存储 | 10GB | 20GB以上 SSD |

### 软件要求

- Python 3.9 - 3.11
- pip 或 conda
- CUDA 11.8+（如使用 GPU）

---

## 快速启动

### 1. 创建虚拟环境（推荐）

```bash
# 使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 或使用 conda
conda create -n pe_ai python=3.10
conda activate pe_ai
```

### 2. 安装依赖

```bash
# 安装 Yolo_backend 依赖
cd Code/Yolo_backend
pip install -r requirements.txt

# 安装 AIChat 依赖
cd ../AIChat
pip install -r requirements.txt
```

### 3. 启动服务

**方式一：分别启动（推荐开发调试）**

```bash
# 终端 1 - 启动 Yolo_backend
cd Code/Yolo_backend
python main.py

# 终端 2 - 启动 AIChat
cd Code/AIChat
python main.py
```

**方式二：后台启动（推荐生产环境）**

```bash
# 后台启动 Yolo_backend
cd Code/Yolo_backend
nohup python main.py > yolo.log 2>&1 &

# 后台启动 AIChat
cd Code/AIChat
nohup python main.py > chat.log 2>&1 &
```

### 4. 验证服务

```bash
# 检查 Yolo_backend
curl http://localhost:8000/health

# 检查 AIChat
curl http://localhost:5000/api/models
```

---

## 模型下载

### Yolo_backend 模型

首次启动会自动下载 YOLOv8-pose 模型（约 10MB）。

### AIChat 模型（Qwen2.5-3B）

**方式一：使用下载脚本（推荐）**

```bash
cd Code/AIChat/finetune
python download_model.py              # 从 ModelScope 下载（国内推荐）
python download_model.py --source huggingface  # 从 HuggingFace 下载
```

**方式二：手动下载**

```bash
# 使用 ModelScope
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2.5-3B-Instruct', cache_dir='./models')"

# 使用 HuggingFace
pip install huggingface_hub
python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-3B-Instruct', local_dir='./models/Qwen2.5-3B-Instruct')"
```

**模型目录结构：**
```
Code/AIChat/models/
├── Qwen2.5-3B-PE-Sports/    # 微调模型（优先使用，约 6GB）
│   ├── config.json
│   ├── model.safetensors
│   └── tokenizer.json
└── Qwen2.5-3B-Instruct/     # 基础模型（回退使用，约 6GB）
    ├── config.json
    ├── model.safetensors
    └── tokenizer.json
```

---

## 微调训练

### 1. 生成训练数据

```bash
cd Code/AIChat/finetune
python generate_training_data.py
```

训练数据生成在 `finetune/data/training_data.jsonl`

### 2. 执行微调训练

```bash
cd Code/AIChat/finetune
python finetune_lora.py
```

训练参数（可根据显存调整）：
- 默认：batch_size=2, gradient_accumulation=4, max_seq_length=1024
- 6GB显存：可直接运行
- 4GB显存：减小 batch_size=1, max_seq_length=512

### 3. 合并 LoRA 权重

```bash
cd Code/AIChat/finetune
python merge_lora.py
```

合并后的模型保存在 `models/Qwen2.5-3B-PE-Sports/`

---

## 详细配置

### Yolo_backend 配置

**端口：** 8000（默认）

**环境变量：**
```bash
# 无需配置，使用默认值即可
```

### AIChat 配置

**端口：** 5000（默认）

**环境变量：**
```bash
# Linux/Mac
export YOLO_BASE_URL=http://localhost:8000
export MODEL_PATH=./models/Qwen2.5-3B-PE-Sports
export MAX_TOKENS=512
export TEMPERATURE=0.7
export LOAD_IN_4BIT=true

# Windows CMD
set YOLO_BASE_URL=http://localhost:8000
set MODEL_PATH=./models/Qwen2.5-3B-PE-Sports
set MAX_TOKENS=512
set TEMPERATURE=0.7
set LOAD_IN_4BIT=true
```

---

## 服务依赖关系

```
启动顺序：
1. Yolo_backend (8000) → 无依赖，独立运行
2. AIChat (5000) → 依赖 Yolo_backend 获取学生运动数据
3. 前端应用 → 调用两个 AI 服务
```

**重要：** 必须先启动 Yolo_backend，再启动 AIChat。

---

## 常见问题

### Q1: Yolo_backend 启动报错 "No module named 'ultralytics'"

```bash
pip install ultralytics
```

### Q2: AIChat 启动报错 "CUDA out of memory"

**解决方案：**
- 使用 4-bit 量化：`set LOAD_IN_4BIT=true`
- 减少生成长度：`set MAX_TOKENS=256`
- 或使用 CPU 推理：`set LOAD_IN_4BIT=false`

### Q3: AIChat 报错 "Model not found"

**解决方案：**
1. 运行下载脚本：`python finetune/download_model.py`
2. 检查模型路径：`./models/Qwen2.5-3B-Instruct/`

### Q4: 微调训练显存不足

**解决方案：**
- 减小参数：`python finetune_lora.py --batch_size=1 --max_seq_length=512`
- 使用更小的模型：Qwen2.5-1.5B

### Q5: 模型下载速度很慢

**解决方案：**
- 使用 ModelScope：`python download_model.py`（国内推荐）
- 设置代理：`export HTTP_PROXY=http://your-proxy:port`