"""
merge_lora.py - 合并 LoRA 权重到基础模型

该脚本将训练好的 LoRA 权重合并到基础模型中，
生成可用于推理的完整模型。

使用方法：
    python merge_lora.py

合并后的模型可以：
1. 直接用于推理
2. 进一步量化
"""

import os
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)


def merge_lora(
    base_model_path: str,
    lora_path: str,
    output_path: str,
):
    """
    合并 LoRA 权重到基础模型。

    参数:
        base_model_path: 基础模型路径
        lora_path: LoRA 权重路径
        output_path: 输出模型路径
    """
    print("=" * 50)
    print("LoRA 模型合并")
    print("=" * 50)
    print(f"基础模型: {base_model_path}")
    print(f"LoRA 权重: {lora_path}")
    print(f"输出路径: {output_path}")
    print("=" * 50)

    # 检查路径
    if not os.path.exists(base_model_path):
        raise FileNotFoundError(f"基础模型不存在: {base_model_path}")
    if not os.path.exists(lora_path):
        raise FileNotFoundError(f"LoRA 权重不存在: {lora_path}")

    # 创建输出目录
    os.makedirs(output_path, exist_ok=True)

    # 加载 Tokenizer
    print("\n加载 Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        base_model_path,
        trust_remote_code=True
    )

    # 使用 4-bit 量化加载基础模型（节省显存）
    print("\n加载基础模型（4-bit 量化）...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    # 加载 LoRA 权重
    print("\n加载 LoRA 权重...")
    model = PeftModel.from_pretrained(
        base_model,
        lora_path,
    )

    # 合并权重
    print("\n合并 LoRA 权重到基础模型...")
    model = model.merge_and_unload()

    # 保存合并后的模型
    print(f"\n保存合并后的模型到 {output_path}...")

    # 由于模型是量化的，我们需要在保存时处理
    # 先将模型移到 CPU，然后保存
    model = model.cpu()
    model.save_pretrained(output_path, safe_serialization=True)
    tokenizer.save_pretrained(output_path)

    print("\n" + "=" * 50)
    print("✓ 合并完成！")
    print("=" * 50)
    print(f"合并后的模型保存至: {output_path}")
    print("\n可直接启动服务：python main.py")


def main():
    parser = argparse.ArgumentParser(description="合并 LoRA 权重")
    parser.add_argument(
        "--base_model",
        type=str,
        default=os.path.join(PROJECT_DIR, "models", "Qwen2.5-3B-Instruct"),
        help="基础模型路径"
    )
    parser.add_argument(
        "--lora_path",
        type=str,
        default=os.path.join(SCRIPT_DIR, "output"),
        help="LoRA 权重路径"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default=os.path.join(PROJECT_DIR, "models", "Qwen2.5-3B-PE-Sports"),
        help="输出模型路径"
    )

    args = parser.parse_args()

    merge_lora(
        base_model_path=args.base_model,
        lora_path=args.lora_path,
        output_path=args.output_path,
    )


if __name__ == "__main__":
    main()
