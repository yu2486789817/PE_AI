"""
finetune_lora.py - LoRA 微调脚本

针对 Qwen2.5-3B 优化（6GB 显存即可训练）
训练时间：约 1-2 小时

使用方法:
    python finetune_lora.py

依赖:
    - torch
    - transformers
    - peft
    - datasets
    - accelerate
    - bitsandbytes
"""

import os
import torch
from dataclasses import dataclass, field
from typing import Optional
import json
import time

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    BitsAndBytesConfig,
)
from transformers.trainer_callback import TrainerCallback
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from datasets import Dataset
import argparse

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# ================= 配置 =================
DEFAULT_CONFIG = {
    # 模型路径
    "model_path": os.path.join(PROJECT_DIR, "models", "Qwen2.5-3B-Instruct"),
    "data_path": os.path.join(SCRIPT_DIR, "data", "training_data.jsonl"),
    "output_dir": os.path.join(SCRIPT_DIR, "output"),

    # LoRA 参数
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,

    # 训练参数
    "num_train_epochs": 3,
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 4,
    "learning_rate": 2e-4,
    "max_seq_length": 1024,

    # 量化
    "use_4bit": True,

    # 日志
    "logging_steps": 5,
    "save_steps": 100,
}


# ================= Data Processing =================

def load_dataset(data_path: str) -> Dataset:
    """Load JSONL format training data."""
    data = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    print(f"Loaded {len(data)} training samples")
    return Dataset.from_list(data)


def format_messages(messages: list) -> str:
    """Format messages to ChatML format."""
    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            prompt_parts.append(f"<|im_start|>system\n{content}<|im_end|>\n")
        elif role == "user":
            prompt_parts.append(f"<|im_start|>user\n{content}<|im_end|>\n")
        elif role == "assistant":
            prompt_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>\n")

    prompt_parts.append("<|im_start|>assistant\n")
    return "".join(prompt_parts)


def preprocess_function(examples, tokenizer, max_seq_length):
    """Preprocess data for training."""
    inputs = []
    labels = []

    for messages in examples["messages"]:
        full_text = format_messages(messages)
        assistant_start = full_text.rfind("<|im_start|>assistant\n") + len("<|im_start|>assistant\n")

        tokenized = tokenizer(
            full_text,
            max_length=max_seq_length,
            truncation=True,
            padding=False,
            return_tensors=None
        )

        input_ids = tokenized["input_ids"]
        label_ids = [-100] * len(input_ids)

        assistant_text = ""
        for msg in messages:
            if msg["role"] == "assistant":
                assistant_text = msg["content"]
                break

        if assistant_text:
            prefix_text = full_text[:assistant_start]
            prefix_tokens = tokenizer(prefix_text, add_special_tokens=False)["input_ids"]
            prefix_len = len(prefix_tokens)

            for i in range(prefix_len, len(input_ids)):
                label_ids[i] = input_ids[i]

        inputs.append(input_ids)
        labels.append(label_ids)

    return {
        "input_ids": inputs,
        "labels": labels,
        "attention_mask": [[1] * len(ids) for ids in inputs]
    }


# ================= Training Callback =================

class ProgressCallback(TrainerCallback):
    """Print training progress with ETA."""

    def __init__(self):
        self.start_time = None
        self.total_steps = 0

    def on_train_begin(self, args, state, control, **kwargs):
        self.start_time = time.time()
        self.total_steps = state.max_steps
        print(f"\nTotal steps: {self.total_steps}")
        print("-" * 50)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs and "loss" in logs:
            elapsed = time.time() - self.start_time
            steps_done = state.global_step
            steps_left = self.total_steps - steps_done

            if steps_done > 0:
                eta = (elapsed / steps_done) * steps_left
                eta_min = int(eta // 60)
                eta_sec = int(eta % 60)

                print(f"Step {steps_done}/{self.total_steps} | "
                      f"Loss: {logs['loss']:.4f} | "
                      f"ETA: {eta_min}m {eta_sec}s")


# ================= Main =================

def main():
    parser = argparse.ArgumentParser(description="LoRA Fine-tuning")
    parser.add_argument("--model_path", type=str, default=DEFAULT_CONFIG["model_path"])
    parser.add_argument("--data_path", type=str, default=DEFAULT_CONFIG["data_path"])
    parser.add_argument("--output_dir", type=str, default=DEFAULT_CONFIG["output_dir"])
    parser.add_argument("--epochs", type=int, default=DEFAULT_CONFIG["num_train_epochs"])
    parser.add_argument("--batch_size", type=int, default=DEFAULT_CONFIG["per_device_train_batch_size"])
    parser.add_argument("--grad_accum", type=int, default=DEFAULT_CONFIG["gradient_accumulation_steps"])
    parser.add_argument("--learning_rate", type=float, default=DEFAULT_CONFIG["learning_rate"])
    parser.add_argument("--lora_r", type=int, default=DEFAULT_CONFIG["lora_r"])
    parser.add_argument("--max_seq_length", type=int, default=DEFAULT_CONFIG["max_seq_length"])
    parser.add_argument("--use_4bit", action="store_true", default=True)
    args = parser.parse_args()

    print("=" * 50)
    print("LoRA Fine-tuning Configuration")
    print("=" * 50)
    print(f"Model: {args.model_path}")
    print(f"Data: {args.data_path}")
    print(f"Output: {args.output_dir}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"Gradient accumulation: {args.grad_accum}")
    print(f"Effective batch size: {args.batch_size * args.grad_accum}")
    print(f"Learning rate: {args.learning_rate}")
    print(f"LoRA rank: {args.lora_r}")
    print(f"Max sequence length: {args.max_seq_length}")
    print(f"4-bit quantization: {args.use_4bit}")
    print("=" * 50)

    # Check GPU
    if not torch.cuda.is_available():
        raise RuntimeError("GPU required for training!")

    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"\nGPU: {gpu_name}")
    print(f"VRAM: {gpu_memory:.1f} GB")

    # Memory check
    if gpu_memory < 7:
        print("\nWarning: GPU memory < 7GB, training may fail.")
        print("Try reducing max_seq_length to 512 or use a smaller model.")

    # Clear cache
    torch.cuda.empty_cache()

    # Load tokenizer
    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_path,
        trust_remote_code=True,
        use_fast=False
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model with 4-bit quantization
    print("\nLoading model (4-bit quantization)...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )

    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)

    # Configure LoRA
    print("\nConfiguring LoRA...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_r * 2,
        lora_dropout=0.05,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        bias="none",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Enable gradient checkpointing
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    # Load data
    print("\nLoading training data...")
    dataset = load_dataset(args.data_path)

    # Preprocess
    print("Preprocessing data...")

    def preprocess_fn(examples):
        return preprocess_function(examples, tokenizer, args.max_seq_length)

    tokenized_dataset = dataset.map(
        preprocess_fn,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Preprocessing"
    )

    # Calculate training steps
    num_samples = len(tokenized_dataset)
    effective_batch = args.batch_size * args.grad_accum
    steps_per_epoch = num_samples // effective_batch
    total_steps = steps_per_epoch * args.epochs

    print(f"\nDataset size: {num_samples}")
    print(f"Steps per epoch: {steps_per_epoch}")
    print(f"Total training steps: {total_steps}")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.05,
        warmup_steps=10,
        logging_steps=5,
        save_steps=100,
        save_total_limit=2,
        fp16=True,
        bf16=False,
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        report_to="none",
        remove_unused_columns=False,
        dataloader_pin_memory=False,
        dataloader_num_workers=0,
    )

    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
        callbacks=[ProgressCallback()],
    )

    # Train
    print("\n" + "=" * 50)
    print("Starting training...")
    print("=" * 50)

    start_time = time.time()
    trainer.train()
    elapsed = time.time() - start_time

    # Save
    print("\nSaving LoRA weights...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    print("\n" + "=" * 50)
    print("Training Complete!")
    print("=" * 50)
    print(f"Training time: {int(elapsed // 60)}m {int(elapsed % 60)}s")
    print(f"LoRA weights saved to: {args.output_dir}")
    print("\nNext step: python finetune/merge_lora.py")


if __name__ == "__main__":
    main()
