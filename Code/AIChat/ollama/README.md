# Ollama 模型导入指南

本指南说明如何将微调后的 Qwen2.5-3B-PE-Sports 模型导入到 Ollama。

## 前置条件

1. 已安装 Ollama（访问 https://ollama.com/download）
2. 已安装 conda 环境 `pe_ai`
3. 有足够的磁盘空间（约 15GB）

## 完整转换流程

### 步骤 1：下载 llama.cpp

```bash
# 下载 CUDA 12 版本（推荐）
# 访问 https://github.com/ggml-org/llama.cpp/releases
# 下载 llama-xxx-win-x64-cuda12.zip

# 解压到 ollama 目录，重命名为 llama.cpp
# 最终路径：Code/AIChat/ollama/llama.cpp/
```

### 步骤 2：下载转换脚本

```bash
cd ollama/llama.cpp
curl -L -o convert_hf_to_gguf.py https://raw.githubusercontent.com/ggml-org/llama.cpp/master/convert_hf_to_gguf.py
```

### 步骤 3：安装 Python 依赖

```bash
conda activate pe_ai
pip install gguf==0.18.0 sentencepiece protobuf transformers torch
```

### 步骤 4：反量化模型（如果模型是 4-bit 量化格式）

微调后的模型如果是 bitsandbytes 4-bit 量化格式，需要先反量化：

```bash
cd Code/AIChat/finetune

python dequantize_model.py \
  --input "G:\...\Code\AIChat\models\Qwen2.5-3B-PE-Sports" \
  --output "G:\...\Code\AIChat\models\Qwen2.5-3B-PE-Sports-fp16"
```

### 步骤 5：转换为 GGUF f16 格式

```bash
cd ollama/llama.cpp

python convert_hf_to_gguf.py \
  "G:\...\Code\AIChat\models\Qwen2.5-3B-PE-Sports-fp16" \
  --outfile "G:\...\Code\AIChat\ollama\gguf\qwen2.5-pe-sports.f16.gguf" \
  --outtype f16
```

### 步骤 6：量化为 Q4_K_M 格式

```bash
llama-quantize.exe \
  "G:\...\Code\AIChat\ollama\gguf\qwen2.5-pe-sports.f16.gguf" \
  "G:\...\Code\AIChat\models\qwen2.5-pe-sports.q4_k_m.gguf" \
  Q4_K_M
```

### 步骤 7：导入 Ollama

```bash
cd Code/AIChat/ollama
ollama create qwen2.5-pe-sports -f Modelfile
```

### 步骤 8：验证

```bash
ollama list
ollama run qwen2.5-pe-sports "你好"
```

## 文件大小参考

| 阶段 | 文件 | 大小 |
|------|------|------|
| 原始模型 | Qwen2.5-3B-PE-Sports | ~2GB |
| 反量化后 | Qwen2.5-3B-PE-Sports-fp16 | ~6GB |
| GGUF f16 | qwen2.5-pe-sports.f16.gguf | ~6.3GB |
| GGUF Q4_K_M | qwen2.5-pe-sports.q4_k_m.gguf | ~2GB |

## 清理中间文件

导入成功后，可删除中间文件节省空间：

```bash
# 删除反量化模型和 f16 GGUF（节省约 12GB）
rm -rf models/Qwen2.5-3B-PE-Sports-fp16
rm -rf ollama/gguf/qwen2.5-pe-sports.f16.gguf
rm -rf ollama/llama.cpp
```

## 常见问题

### Q: AttributeError: GEMMA4 / MISTRAL4

gguf 版本与转换脚本不兼容，需要修改 `convert_hf_to_gguf.py`：
- `GEMMA4` → `GEMMA`
- `MISTRAL4` → `DEEPSEEK2`
- `HUNYUAN_VL` → `HUNYUAN_DENSE`

### Q: ValueError: Can not map tensor 'xxx.absmax'

模型是 4-bit 量化格式，需要先运行 `dequantize_model.py`。

### Q: 模型生成被截断

增加 `MAX_TOKENS` 配置或 Modelfile 中的 `num_predict` 参数。
