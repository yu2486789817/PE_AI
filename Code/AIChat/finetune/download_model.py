"""
download_model.py - 下载 Qwen2.5-3B-Instruct 模型

使用方法:
    python download_model.py                    # 默认从 ModelScope 下载
    python download_model.py --source huggingface  # 从 HuggingFace 下载
"""

import os
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "models")

# 模型配置
MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"


def download_from_modelscope():
    """从 ModelScope 下载（国内推荐）"""
    from modelscope import snapshot_download

    model_dir = os.path.join(MODELS_DIR, "Qwen2.5-3B-Instruct")

    print("=" * 60)
    print("下载 Qwen2.5-3B-Instruct 模型 (ModelScope)")
    print("=" * 60)
    print(f"模型 ID: {MODEL_ID}")
    print(f"保存路径: {model_dir}")
    print("模型大小约 6GB，请耐心等待...")
    print("=" * 60)

    os.makedirs(MODELS_DIR, exist_ok=True)

    snapshot_download(
        MODEL_ID,
        cache_dir=MODELS_DIR,
        local_dir=model_dir
    )

    print("\n" + "=" * 60)
    print("下载完成!")
    print("=" * 60)
    print(f"模型路径: {model_dir}")
    print("\n下一步: python finetune/generate_training_data.py")

    return model_dir


def download_from_huggingface():
    """从 HuggingFace 下载"""
    from huggingface_hub import snapshot_download

    model_dir = os.path.join(MODELS_DIR, "Qwen2.5-3B-Instruct")

    print("=" * 60)
    print("下载 Qwen2.5-3B-Instruct 模型 (HuggingFace)")
    print("=" * 60)
    print(f"模型 ID: {MODEL_ID}")
    print(f"保存路径: {model_dir}")
    print("=" * 60)

    os.makedirs(MODELS_DIR, exist_ok=True)

    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=model_dir
    )

    print("\n" + "=" * 60)
    print("下载完成!")
    print("=" * 60)
    print(f"模型路径: {model_dir}")

    return model_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下载 Qwen2.5-3B-Instruct 模型")
    parser.add_argument(
        "--source",
        choices=["modelscope", "huggingface"],
        default="modelscope",
        help="下载源（默认 modelscope，国内速度更快）"
    )

    args = parser.parse_args()

    if args.source == "modelscope":
        download_from_modelscope()
    else:
        download_from_huggingface()
