"""
dequantize_model.py - 将量化模型转换为非量化格式

该脚本将 bitsandbytes 4-bit 量化的模型转换为标准的 FP16 格式，
以便后续转换为 GGUF 格式导入 Ollama。

使用方法：
    python dequantize_model.py
"""

import os
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def dequantize_model(
    quantized_model_path: str,
    output_path: str,
):
    """
    将量化模型转换为 FP16 格式。

    参数:
        quantized_model_path: 量化模型路径
        output_path: 输出模型路径
    """
    print("=" * 50)
    print("模型反量化")
    print("=" * 50)
    print(f"量化模型: {quantized_model_path}")
    print(f"输出路径: {output_path}")
    print("=" * 50)

    # 检查路径
    if not os.path.exists(quantized_model_path):
        raise FileNotFoundError(f"量化模型不存在: {quantized_model_path}")

    # 创建输出目录
    os.makedirs(output_path, exist_ok=True)

    # 加载 Tokenizer
    print("\n加载 Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        quantized_model_path,
        trust_remote_code=True
    )

    # 使用 4-bit 量化加载模型（因为源模型是量化的）
    print("\n加载量化模型...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        quantized_model_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    # 反量化：将模型转换为 FP16
    print("\n反量化模型到 FP16...")
    model = model.dequantize()

    # 移到 CPU
    print("移至 CPU...")
    model = model.cpu()

    # 转换为 float16
    print("转换为 float16...")
    model = model.to(torch.float16)

    # 保存为 FP16 格式
    print(f"\n保存 FP16 模型到 {output_path}...")

    # 手动保存 state_dict
    state_dict = model.state_dict()
    torch.save(state_dict, os.path.join(output_path, "pytorch_model.bin"))

    # 保存 config
    model.config.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    print("\n" + "=" * 50)
    print("✓ 反量化完成！")
    print("=" * 50)
    print(f"FP16 模型保存至: {output_path}")
    print("\n下一步：使用 llama.cpp 转换为 GGUF 格式")


def main():
    parser = argparse.ArgumentParser(description="将量化模型转换为 FP16 格式")
    parser.add_argument(
        "--input",
        type=str,
        default="G:/Third_year_second_semester/SoftwareEngineeringManagementAndEconomics/PE_AI/Code/AIChat/models/Qwen2.5-3B-PE-Sports",
        help="量化模型路径"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="G:/Third_year_second_semester/SoftwareEngineeringManagementAndEconomics/PE_AI/Code/AIChat/models/Qwen2.5-3B-PE-Sports-fp16",
        help="输出 FP16 模型路径"
    )

    args = parser.parse_args()

    dequantize_model(
        quantized_model_path=args.input,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
