# LoRA 微调指南

本目录包含用于微调大语言模型的脚本和训练数据，使其更适合体育教学场景。

## 目录结构

```
finetune/
├── data/                       # 训练数据目录
│   └── training_data.jsonl     # 训练数据文件
├── output/                     # LoRA 权重输出目录
├── download_model.py           # 模型下载脚本
├── generate_training_data.py   # 训练数据生成脚本
├── finetune_lora.py            # LoRA 微调脚本
├── merge_lora.py               # 模型合并脚本
└── README.md                   # 本文档
```

## 快速开始

### 完整微调流程

```bash
# 激活环境
conda activate pe_ai
cd Code/AIChat

# 步骤 1：下载基础模型（约 15GB，需 10-30 分钟）
python finetune/download_model.py

# 步骤 2：生成训练数据
python finetune/generate_training_data.py

# 步骤 3：运行 LoRA 微调（约 1-2 小时）
python finetune/finetune_lora.py

# 步骤 4：合并 LoRA 权重
python finetune/merge_lora.py

# 步骤 5：重启 AIChat 服务（自动使用微调模型）
python main.py
```

## 详细说明

### 步骤 1：下载基础模型

**脚本：** `download_model.py`

**模型信息：**
- 模型：Qwen2.5-7B-Instruct
- 大小：约 15GB
- 来源：ModelScope（国内镜像）

**命令：**
```bash
python finetune/download_model.py
```

**输出：**
```
模型下载完成！
Model saved to: ./models/Qwen/Qwen2___5-7B-Instruct
```

### 步骤 2：生成训练数据

**脚本：** `generate_training_data.py`

**数据内容：**
| 类别 | 数量 | 说明 |
|------|------|------|
| 学生教练问答 | ~25 | 动作纠正、训练建议、运动知识 |
| 教师助理问答 | ~8 | 班级分析、教学方案 |
| 上下文分析 | ~4 | 带运动数据的分析 |
| 多轮对话 | ~2 | 复杂对话场景 |

**命令：**
```bash
python finetune/generate_training_data.py
```

**输出：**
```
生成训练数据完成！
文件: ./finetune/data/training_data.jsonl
样本数: 40
```

**数据格式：**
```json
{
    "messages": [
        {"role": "system", "content": "你是一个高校体育教学平台的私人教练AI..."},
        {"role": "user", "content": "我最近做俯卧撑正确率只有60%，怎么改进？"},
        {"role": "assistant", "content": "同学你好！俯卧撑正确率60%说明基础还是有的..."}
    ]
}
```

### 步骤 3：运行 LoRA 微调

**脚本：** `finetune_lora.py`

**优化配置（针对 8GB 显存）：**
| 参数 | 值 | 说明 |
|------|-----|------|
| lora_r | 8 | LoRA 秩 |
| batch_size | 1 | 批次大小 |
| grad_accum | 8 | 梯度累积 |
| max_seq_length | 1024 | 最大序列长度 |
| use_4bit | True | 4-bit 量化 |

**命令：**
```bash
python finetune/finetune_lora.py
```

**自定义参数：**
```bash
python finetune/finetune_lora.py \
    --epochs 5 \
    --learning_rate 1e-4 \
    --lora_r 16 \
    --max_seq_length 512
```

**输出示例：**
```
==================================================
LoRA Fine-tuning Configuration
==================================================
Model: ./models/Qwen/Qwen2___5-7B-Instruct
Data: ./finetune/data/training_data.jsonl
Output: ./finetune/output
Epochs: 3
Batch size: 1
Gradient accumulation: 8
Effective batch size: 8
Learning rate: 0.0002
LoRA rank: 8
Max sequence length: 1024
4-bit quantization: True
==================================================

GPU: NVIDIA GeForce RTX 4060 Laptop GPU
VRAM: 8.0 GB

Loading tokenizer...
Loading model (4-bit quantization)...

Step 5/15 | Loss: 2.3456 | ETA: 45m 30s
Step 10/15 | Loss: 1.8765 | ETA: 22m 15s
Step 15/15 | Loss: 1.5432 | ETA: 0m 0s

Training Complete!
Training time: 67m 45s
LoRA weights saved to: ./finetune/output
```

### 步骤 4：合并 LoRA 权重

**脚本：** `merge_lora.py`

**命令：**
```bash
python finetune/merge_lora.py
```

**输出：**
```
==================================================
LoRA 模型合并
==================================================
基础模型: ./models/Qwen/Qwen2___5-7B-Instruct
LoRA 权重: ./finetune/output
输出路径: ./models/Qwen2.5-7B-PE-Sports
==================================================

加载 Tokenizer...
加载基础模型（4-bit 量化）...
加载 LoRA 权重...
合并 LoRA 权重到基础模型...
保存合并后的模型...

✓ 合并完成！
合并后的模型保存至: ./models/Qwen2.5-7B-PE-Sports
```

### 步骤 5：使用微调模型

**自动检测：**
AIChat 服务启动时会自动检测并使用微调模型：
1. 优先：`./models/Qwen2.5-7B-PE-Sports`（微调模型）
2. 回退：`./models/Qwen/Qwen2___5-7B-Instruct`（基础模型）

**启动服务：**
```bash
python main.py
```

**验证：**
服务启动时会显示使用的模型路径：
```
Loading local model: ./models/Qwen2.5-7B-PE-Sports
Quantization: 4-bit=True, 8-bit=False
Model loaded successfully
```

## 显存需求

| 阶段 | 配置 | 显存需求 |
|------|------|----------|
| 微调 | 4-bit + LoRA r=8 | ~6GB |
| 微调 | 4-bit + LoRA r=16 | ~8GB |
| 推理 | 4-bit 量化 | ~5GB |
| 推理 | 8-bit 量化 | ~7GB |
| 推理 | FP16 | ~14GB |

## 参数调优

### 提高训练质量

```bash
# 增加训练轮数
python finetune/finetune_lora.py --epochs 5

# 增加 LoRA 秩（需要更多显存）
python finetune/finetune_lora.py --lora_r 16

# 降低学习率（更稳定）
python finetune/finetune_lora.py --learning_rate 1e-4
```

### 减少显存占用

```bash
# 减小序列长度
python finetune/finetune_lora.py --max_seq_length 512

# 减小 LoRA 秩
python finetune/finetune_lora.py --lora_r 4

# 增加梯度累积（保持有效批次大小）
python finetune/finetune_lora.py --grad_accum 16
```

## 扩展训练数据

编辑 `generate_training_data.py` 添加更多训练样本：

```python
# 在 generate_student_coach_data() 中添加
{
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT_STUDENT},
        {"role": "user", "content": "你的问题"},
        {"role": "assistant", "content": "你的回答"}
    ]
}
```

然后重新生成数据并微调：
```bash
python finetune/generate_training_data.py
python finetune/finetune_lora.py
python finetune/merge_lora.py
```

## 常见问题

### Q: CUDA out of memory

A: 尝试以下方法：
1. 减小 `--max_seq_length`（如 512）
2. 减小 `--lora_r`（如 4）
3. 确保 `--use_4bit` 已启用
4. 关闭其他占用 GPU 的程序

### Q: 训练 loss 不下降

A: 可能原因：
1. 学习率过大 → 减小 `--learning_rate`
2. LoRA 秩过小 → 增大 `--lora_r`
3. 数据质量问题 → 检查训练数据格式

### Q: 模型输出质量不好

A: 尝试：
1. 增加训练轮数 `--epochs`
2. 增加训练数据量
3. 调整 LoRA 秩 `--lora_r`

### Q: 合并时出现警告

A: 警告 "copying from a non-meta parameter" 是正常的，不影响合并结果。这是因为显存不足导致部分参数被卸载到 CPU。

## 文件说明

| 文件 | 说明 |
|------|------|
| `download_model.py` | 从 ModelScope 下载基础模型 |
| `generate_training_data.py` | 生成体育教学领域训练数据 |
| `finetune_lora.py` | LoRA 微调脚本（4-bit 量化） |
| `merge_lora.py` | 合并 LoRA 权重到基础模型 |

## 参考资源

- [Qwen 官方文档](https://github.com/QwenLM/Qwen)
- [PEFT 文档](https://huggingface.co/docs/peft)
- [LoRA 论文](https://arxiv.org/abs/2106.09685)
