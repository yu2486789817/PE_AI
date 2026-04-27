"""
chat_module.py - AI 聊天核心模块

功能：
1. 本地 LLM 模型加载与推理（Qwen2.5-3B）
2. 会话管理（创建、查询、删除、消息存储）
3. 会话导出

模型配置：
- 微调模型: ./models/Qwen2.5-3B-PE-Sports
- 量化: 4-bit (默认)
"""

import os
import time
import sqlite3
import tempfile
import logging
import json
from typing import Dict, List, Optional

import requests
from database import init_db, DB_PATH

# ================= 日志配置 =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================= 路径配置 =================
# 获取当前脚本所在目录，确保无论在哪里运行都使用正确的路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= 模型配置 =================
# 只使用微调模型
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "auto").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
FINETUNED_MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "Qwen2.5-3B-PE-Sports")
BASE_MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "Qwen2.5-3B-Instruct")
MODEL_PATH = os.getenv("MODEL_PATH", FINETUNED_MODEL_PATH)
AVAILABLE_MODELS = [
    item.strip()
    for item in os.getenv(
        "AVAILABLE_MODELS",
        f"ollama:{OLLAMA_MODEL},local:Qwen2.5-3B-PE-Sports,local:Qwen2.5-3B-Instruct"
    ).split(",")
    if item.strip()
]
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "256"))
TITLE_MAX_TOKENS = int(os.getenv("TITLE_MAX_TOKENS", "32"))
LOAD_IN_4BIT = os.getenv("LOAD_IN_4BIT", "true").lower() == "true"
LOAD_IN_8BIT = os.getenv("LOAD_IN_8BIT", "false").lower() == "true"
USE_CPU_OFFLOAD = os.getenv("USE_CPU_OFFLOAD", "false").lower() == "true"
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "1024"))  # 减少输入长度

# ================= 系统提示词 =================
SYSTEM_PROMPTS = {
    "student_coach": """你是大学体育平台的AI私教。学生数据：{context}

回答要求：
- 简洁专业，不超过80字
- 直接回答问题，不要废话
- 针对学生具体情况给出建议
""",

    "teacher_assistant": """你是大学体育平台的AI教学助理。

回答要求：
- 专业简洁，不超过100字
- 直接回答问题，不要废话
- 提供具体数据或建议
"""
}


# ================= 本地 LLM 类 =================

class LocalLLM:
    """
    本地 LLM 管理类，使用 Transformers 后端。

    特性：
    - 4-bit/8-bit 量化支持
    - 自动设备映射
    - ChatML 提示词格式
    """

    _instance = None
    _model = None
    _tokenizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is not None:
            return
        self._load_model()

    def _load_model(self):
        """加载本地模型。"""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        print(f"Loading local model: {MODEL_PATH}")
        print(f"Quantization: 4-bit={LOAD_IN_4BIT}, 8-bit={LOAD_IN_8BIT}, CPU_offload={USE_CPU_OFFLOAD}")

        # 加载 tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(
            MODEL_PATH, trust_remote_code=True, use_fast=False
        )
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        # 配置量化
        model_config_path = os.path.join(MODEL_PATH, "config.json")
        model_has_quantization_config = False
        if os.path.exists(model_config_path):
            try:
                with open(model_config_path, "r", encoding="utf-8") as f:
                    model_has_quantization_config = "quantization_config" in json.load(f)
            except Exception:
                model_has_quantization_config = False

        quantization_config = None
        if LOAD_IN_4BIT and not model_has_quantization_config:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True
            )
        elif LOAD_IN_8BIT and not model_has_quantization_config:
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)

        # 加载模型
        model_kwargs = {
            "pretrained_model_name_or_path": MODEL_PATH,
            "trust_remote_code": True,
        }

        # 设备映射策略
        if LOAD_IN_4BIT and torch.cuda.is_available() and not USE_CPU_OFFLOAD:
            # bitsandbytes 4-bit models cannot be split to CPU/disk by device_map="auto".
            model_kwargs["device_map"] = {"": 0}
        elif USE_CPU_OFFLOAD:
            # CPU 卸载模式：部分层放到 CPU，降低显存占用
            model_kwargs["device_map"] = "auto"
            model_kwargs["max_memory"] = {0: "6GB", "cpu": "8GB"}  # 限制 GPU 显存使用
        else:
            model_kwargs["device_map"] = "auto"

        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        else:
            model_kwargs["torch_dtype"] = torch.float16

        print(f"Device map: {model_kwargs.get('device_map')}")
        self._model = AutoModelForCausalLM.from_pretrained(**model_kwargs)

        # 尝试启用 BetterTransformer 加速（Windows 兼容）
        try:
            self._model = self._model.to_bettertransformer()
            logger.info("BetterTransformer 加速已启用")
        except Exception as e:
            logger.warning(f"BetterTransformer 不可用: {e}")

        self._model.eval()

        # 打印模型信息
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"GPU Memory: {gpu_memory:.1f} GB total, {allocated:.1f} GB used")

        print("Model loaded successfully")

    def predict(self, messages: List[Dict], max_tokens: int = None, temperature: float = None) -> str:
        """生成回复。"""
        import torch
        import time

        start_time = time.time()
        temperature = temperature or TEMPERATURE

        prompt = self._build_prompt(messages)
        t1 = time.time()

        # 截断输入，避免过长导致显存溢出
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            return_attention_mask=True,
            truncation=True,
            max_length=MAX_INPUT_LENGTH
        )
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

        t2 = time.time()
        logger.info(f"[性能] Tokenize 耗时: {t2-t1:.2f}s, 输入长度: {inputs['input_ids'].shape[1]}")

        # 推理前清理缓存
        torch.cuda.empty_cache()

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens or MAX_TOKENS,
                do_sample=False,  # 贪婪解码，更快
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
                repetition_penalty=1.05,
                use_cache=True
            )

        t3 = time.time()
        logger.info(f"[性能] 模型推理耗时: {t3-t2:.2f}s, 生成 token 数: {outputs.shape[1] - inputs['input_ids'].shape[1]}")

        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        response = self._tokenizer.decode(new_tokens, skip_special_tokens=True)

        # 推理后清理缓存
        torch.cuda.empty_cache()

        total_time = time.time() - start_time
        logger.info(f"[性能] predict 总耗时: {total_time:.2f}s")

        return response.strip()

    def _build_prompt(self, messages: List[Dict]) -> str:
        """构建 ChatML 格式提示词。"""
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


# 全局 LLM 实例
class OllamaLLM:
    """Ollama HTTP API client."""

    def __init__(self, model: str = None):
        self.base_url = OLLAMA_BASE_URL.rstrip("/")
        self.model = model or OLLAMA_MODEL

    def predict(self, messages: List[Dict], max_tokens: int = None, temperature: float = None) -> str:
        start_time = time.time()
        options = {
            "temperature": temperature or TEMPERATURE,
        }
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        elif MAX_TOKENS is not None:
            options["num_predict"] = MAX_TOKENS

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "think": False,
                "options": options,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        total_time = time.time() - start_time
        eval_count = data.get("eval_count", 0) or 0
        eval_duration_sec = (data.get("eval_duration", 0) or 0) / 1_000_000_000
        tokens_per_sec = eval_count / eval_duration_sec if eval_duration_sec > 0 else 0
        logger.info(
            "[性能] Ollama 推理耗时: %.2fs, 总耗时: %.2fs, 生成 token 数: %s, 速度: %.2f tok/s",
            eval_duration_sec,
            total_time,
            eval_count,
            tokens_per_sec
        )
        message = data.get("message", {})
        content = message.get("content", "")
        if content:
            return content.strip()
        return message.get("thinking", "").strip()


_llm_instance = None


def _ollama_available() -> bool:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=2)
        return response.ok
    except requests.RequestException:
        return False


def get_model_provider() -> str:
    if MODEL_PROVIDER in ("local", "ollama"):
        return MODEL_PROVIDER
    return "ollama" if _ollama_available() else "local"


def get_available_models() -> List[str]:
    models = []
    for model in AVAILABLE_MODELS:
        lower = model.lower()
        if not lower.startswith("local:"):
            models.append(model)
            continue

        model_name = model.split(":", 1)[1]
        model_path = os.path.join(SCRIPT_DIR, "models", model_name)
        if os.path.exists(model_path):
            models.append(model)

    return models


def _resolve_model_choice(model_name: str) -> tuple[str, str]:
    if not model_name:
        provider = get_model_provider()
        return provider, OLLAMA_MODEL if provider == "ollama" else MODEL_PATH

    value = model_name.strip()
    lower = value.lower()
    if lower.startswith("ollama:"):
        return "ollama", value.split(":", 1)[1]
    if lower == "ollama":
        return "ollama", OLLAMA_MODEL
    if lower.startswith("local:") or "qwen" in lower:
        return "local", MODEL_PATH
    return get_model_provider(), value


def get_llm():
    """获取全局 LLM 实例（延迟加载）。"""
    global _llm_instance
    if _llm_instance is None:
        if get_model_provider() == "ollama":
            _llm_instance = OllamaLLM()
        else:
            _llm_instance = LocalLLM()
    return _llm_instance


def model_predict(model_name: str, messages: List[Dict], max_tokens: int = None) -> str:
    """调用本地模型生成回复。"""
    provider, resolved_model = _resolve_model_choice(model_name)
    llm = OllamaLLM(resolved_model) if provider == "ollama" else LocalLLM()
    return llm.predict(messages, max_tokens=max_tokens)


# ================= 会话管理类 =================

class ChatManager:
    """聊天会话管理类。"""

    def __init__(self):
        init_db()

    def create_session(self, user_id: str, model_name: str = None, role: str = "student") -> int:
        """创建新会话。"""
        title = f"New Chat-{time.strftime('%Y-%m-%d %H:%M')}"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (user_id, title, model, role) VALUES (?, ?, ?, ?)",
            (user_id, title, model_name or get_model_provider(), role)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return session_id

    def get_session_by_user(self, user_id: str) -> Dict:
        """获取用户的最新会话。"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
            (user_id,)
        )
        session_row = cursor.fetchone()

        if not session_row:
            conn.close()
            return None

        cursor.execute(
            "SELECT role, content, model FROM messages WHERE session_id = ? "
            "AND role IN ('user', 'assistant') ORDER BY timestamp",
            (session_row["id"],)
        )
        messages = [{"role": row[0], "content": row[1], "model": row[2]} for row in cursor.fetchall()]

        conn.close()

        return {
            "session_id": session_row["id"],
            "messages": messages,
            "model": session_row["model"],
            "title": session_row["title"],
            "role": session_row["role"]
        }

    def get_session_by_id(self, session_id: int) -> Dict:
        """根据 ID 获取会话。"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session_row = cursor.fetchone()

        if not session_row:
            conn.close()
            return None

        cursor.execute(
            "SELECT role, content, model FROM messages WHERE session_id = ? "
            "AND role IN ('user', 'assistant') ORDER BY timestamp",
            (session_id,)
        )
        messages = [{"role": row[0], "content": row[1], "model": row[2]} for row in cursor.fetchall()]

        conn.close()

        return {
            "session_id": session_row["id"],
            "messages": messages,
            "model": session_row["model"],
            "title": session_row["title"],
            "role": session_row["role"]
        }

    def get_session_messages_with_system(self, session_id: int) -> List[Dict]:
        """获取会话的所有消息（包含 system）。"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]

        conn.close()
        return messages

    def update_session_title(self, session_id: int, user_input: str, model_name: str = None) -> None:
        """生成会话标题。"""
        try:
            prompt = f"Please generate a very short title (no more than 6 characters, no punctuation) based on the user's message:\n\"{user_input}\""
            messages = [{"role": "user", "content": prompt}]
            title = model_predict(None, messages, max_tokens=TITLE_MAX_TOKENS)
            title = title.strip(' " "\'\n').replace('Title:', '').replace('Title：', '')
            if len(title) > 10:
                title = title[:10]
        except Exception as e:
            print(f"Failed to generate title: {e}")
            title = user_input[:10] + "..." if len(user_input) > 10 else user_input

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
        conn.commit()
        conn.close()

    def delete_session(self, session_id: int) -> bool:
        """删除会话。"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def list_sessions_by_user(self, user_id: str) -> List[Dict]:
        """获取用户的所有会话。"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, model, role FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [{"session_id": row[0], "title": row[1], "model": row[2], "role": row[3]} for row in rows]

    def add_message(self, session_id: int, role: str, content: str, model: str = None) -> bool:
        """添加消息。"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (session_id, role, content, model) VALUES (?, ?, ?, ?)",
            (session_id, role, content, model or get_model_provider())
        )

        cursor.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,)
        )

        conn.commit()
        conn.close()
        return True

    def clear_session_messages(self, session_id: int) -> bool:
        """清空会话消息。"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
        return True


def export_markdown(session_id: int, chat_mgr: ChatManager):
    """导出会话为 Markdown 文件。"""
    session = chat_mgr.get_session_by_id(session_id)
    if not session:
        return None

    md_lines = [f"# Chat Export - {session['title']}"]

    for msg in session["messages"]:
        role = "User" if msg["role"] == "user" else "AI"
        md_lines.append(f"**{role}:**\n{msg['content']}\n")

    md_content = "\n\n".join(md_lines)

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md", encoding="utf-8") as f:
        f.write(md_content)
        temp_path = f.name

    return temp_path
