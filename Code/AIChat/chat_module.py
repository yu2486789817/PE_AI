"""
chat_module.py - AI 聊天核心模块

功能：
1. Ollama API 调用（使用微调后的 Qwen2.5-3B-PE-Sports 模型）
2. 会话管理（创建、查询、删除、消息存储）
3. 会话导出

模型配置：
- Ollama 服务地址: http://localhost:11434
- 模型名称: qwen2.5-pe-sports（需先导入到 Ollama）
"""

import os
import time
import sqlite3
import tempfile
import logging
import requests
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
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= 模型配置 =================
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")
AVAILABLE_MODELS = os.getenv("AVAILABLE_MODELS", "qwen2.5-pe-sports").split(",")
TITLE_MAX_TOKENS = int(os.getenv("TITLE_MAX_TOKENS", "20"))

# ================= Ollama 配置 =================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-pe-sports")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.9"))

# ================= 系统提示词 =================
SYSTEM_PROMPTS = {
    "student_coach": """你是大学体育平台的AI私教。学生数据：{context}

回答要求：
- 简洁专业，不超过300字
- 直接回答问题，不要废话
- 针对学生具体情况给出建议
""",

    "teacher_assistant": """你是大学体育平台的AI教学助理。

回答要求：
- 专业简洁，不超过300字
- 直接回答问题，不要废话
- 提供具体数据或建议
"""
}


# ================= Ollama LLM 类 =================

class OllamaLLM:
    """
    Ollama LLM 管理类，通过 HTTP API 调用 Ollama 服务。

    特性：
    - 无需本地加载模型，由 Ollama 服务管理
    - 支持流式和非流式响应
    - 自动处理 ChatML 格式
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._check_ollama_service()

    def _check_ollama_service(self):
        """检查 Ollama 服务是否可用。"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                # 检查模型是否存在（支持带或不带 :latest 后缀）
                model_found = any(
                    name == OLLAMA_MODEL or name.startswith(f"{OLLAMA_MODEL}:")
                    for name in model_names
                )
                logger.info(f"Ollama 服务可用，已加载模型: {model_names}")
                if not model_found:
                    logger.warning(f"模型 {OLLAMA_MODEL} 未在 Ollama 中找到，请先导入模型")
            else:
                logger.warning(f"Ollama 服务响应异常: {response.status_code}")
        except Exception as e:
            logger.warning(f"无法连接 Ollama 服务 ({OLLAMA_BASE_URL}): {e}")

    def predict(self, messages: List[Dict], max_tokens: int = None, temperature: float = None) -> str:
        """生成回复。"""
        start_time = time.time()
        temperature = temperature or TEMPERATURE

        # 调用 Ollama API
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                total_time = time.time() - start_time
                logger.info(f"[性能] Ollama 推理耗时: {total_time:.2f}s")
                return content.strip()
            else:
                error_msg = f"Ollama API 错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return f"Error: {error_msg}"

        except requests.exceptions.Timeout:
            return "Error: Ollama 请求超时"
        except requests.exceptions.ConnectionError:
            return "Error: 无法连接 Ollama 服务"
        except Exception as e:
            logger.error(f"Ollama 推理异常: {e}")
            return f"Error: {str(e)}"


# 全局 LLM 实例
_llm_instance: Optional[OllamaLLM] = None

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

def get_llm() -> OllamaLLM:
    """获取全局 LLM 实例（延迟加载）。"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = OllamaLLM()
    return _llm_instance


def model_predict(model_name: str, messages: List[Dict], max_tokens: int = None) -> str:
    """调用 Ollama 模型生成回复。"""
    try:
        llm = get_llm()
        return llm.predict(messages, max_tokens=max_tokens)
    except Exception as e:
        return f"Error: {str(e)}"


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
