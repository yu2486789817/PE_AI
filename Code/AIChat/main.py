"""
AIChat - AI 聊天助手服务主入口 (本地模型版)

该模块是 AI 聊天服务的 FastAPI 应用入口，提供：
1. 会话管理 API：创建、查询、删除聊天会话
2. 消息发送 API：发送消息并获取 AI 回复
3. AI 分析报告 API：生成和查询运动数据分析报告

服务架构：
- 端口：5000
- 数据库：SQLite (chat_history.db)
- 依赖服务：Yolo_backend (端口 8000) - 获取学生运动数据
- 本地模型：Qwen2.5-3B-Instruct + LoRA 微调 (自动检测)

模型配置：
- 优先使用微调模型: ./models/Qwen2.5-3B-PE-Sports
- 回退基础模型: ./models/Qwen2.5-3B-Instruct
- 默认量化: 4-bit (可通过环境变量配置)

API 接口设计：
- /api/sessions: 会话 CRUD 操作
- /api/sessions/{id}/messages: 消息发送
- /api/analysis: AI 分析报告生成与查询
"""

import os
import json
import logging
from typing import Dict, List

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from database import init_db

# 导入聊天模块
from chat_module import (
    SYSTEM_PROMPTS,
    ChatManager,
    model_predict,
    export_markdown
)

# 导入报告模块
from report_module import (
    AI_PROMPTS,
    generate_analysis_report,
    query_analysis_report,
    get_recent_analyses,
    get_yolo_student_all_records,
    _parse_feedback_json
)

# ================= 日志配置 =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================= FastAPI 应用初始化 =================
app = FastAPI(
    title="AI Chat API",
    description="AI聊天后端API - 提供智能对话和运动数据分析功能",
    version="1.0.0"
)

# 配置 CORS 中件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                    # 允许所有来源
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# 初始化聊天管理器（全局单例）
chat_mgr = ChatManager()

# 应用启动时初始化数据库
init_db()


@app.on_event("startup")
async def startup_event():
    """应用启动时预加载 LLM 模型。"""
    from chat_module import get_llm
    logger.info("预加载 LLM 模型...")
    get_llm()
    logger.info("LLM 模型加载完成")

# ================= 会话管理 API =================

@app.get('/api/sessions')
async def list_sessions(user_id: str):
    """
    获取指定用户的所有会话列表。

    参数:
        user_id: 用户ID（查询参数）

    返回:
        JSONResponse: {
            "success": true,
            "data": [{"session_id": 1, "title": "...", "model": "Qwen"}, ...]
        }
    """
    try:
        if not user_id:
            logger.warning("list_sessions: 用户ID为空")
            return JSONResponse({
                "success": False,
                "error": "用户ID不能为空"
            }, status_code=400)

        sessions = chat_mgr.list_sessions_by_user(user_id)
        logger.info(f"list_sessions: 查询用户 {user_id} 的会话，共 {len(sessions)} 个")
        return JSONResponse({
            "success": True,
            "data": sessions
        })
    except Exception as e:
        logger.error(f"list_sessions 错误: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post('/api/sessions')
async def create_session(request: Request):
    """
    为指定用户创建新会话。

    请求体:
        {
            "user_id": "student001",     // 必填：用户ID
            "model": "Qwen",             // 可选：模型名称，默认 Qwen
            "role": "student"            // 可选：用户角色（student/teacher）
        }

    处理流程:
        1. 验证用户ID和模型
        2. 创建会话记录
        3. 根据角色设置不同的 System Prompt
        4. 发送欢迎消息

    返回:
        JSONResponse: {
            "success": true,
            "data": {
                "session_id": 1,
                "session": {...},
                "welcome_message": {"role": "assistant", "content": "..."}
            }
        }
    """
    try:
        data = await request.json()
        user_id = data.get('user_id')
        model_name = data.get('model')      # 模型是可选的，默认值在 ChatManager 中处理
        role = data.get('role', 'student')  # 获取用户角色

        logger.info(f"create_session: user_id={user_id}, role={role}")

        if not user_id:
            logger.warning("create_session: 用户ID为空")
            return JSONResponse({
                "success": False,
                "error": "用户ID不能为空"
            }, status_code=400)

        # 创建会话（传递 role 参数）
        session_id = chat_mgr.create_session(user_id, model_name, role)
        session = chat_mgr.get_session_by_id(session_id)
        logger.info(f"create_session: 创建会话成功，session_id={session_id}")

        # ========== 根据角色设置 System Prompt ==========
        if role == 'teacher':
            # 教师角色：使用教学助理 Prompt
            system_prompt = SYSTEM_PROMPTS["teacher_assistant"]
            welcome_msg_content = "老师您好，我是您的专属AI教学助理。我可以帮您分析全班同学的运动表现数据，或提供教案优化建议。今天需要我帮您做些什么？"
        else:
            # 学生角色：使用私人教练 Prompt，并注入历史运动数据
            context_str = "暂无近期运动数据记录。"
            try:
                # 从 Yolo_backend 获取学生历史运动数据
                records = get_yolo_student_all_records(user_id)
                if records and isinstance(records, list) and len(records) > 0:
                    # 解析 feedback_json 字段，避免双重编码
                    records = _parse_feedback_json(records)
                    # 取最近的5条记录以避免 Prompt 过长
                    recent_records = records[-5:]
                    context_str = json.dumps(recent_records, ensure_ascii=False)
                    logger.info(f"create_session: 获取学生 {user_id} 历史记录 {len(records)} 条")
            except Exception as e:
                # 获取失败不影响会话创建，使用默认提示
                logger.warning(f"create_session: 获取学生历史运动记录失败（Yolo_backend 可能未启动）: {e}")

            system_prompt = SYSTEM_PROMPTS["student_coach"].format(context=context_str)
            welcome_msg_content = "你好！我是你的专属AI运动私教。我已经同步了你近期的运动考核数据，随时可以为你提供定制化的训练指导和动作纠正建议。今天想练点什么？"

        # 添加 System Prompt 和欢迎消息
        chat_mgr.add_message(session_id, "system", system_prompt, model_name)

        welcome_msg = {
            "role": "assistant",
            "content": welcome_msg_content
        }
        chat_mgr.add_message(session_id, "assistant", welcome_msg["content"], model_name)

        return JSONResponse({
            "success": True,
            "data": {
                "session_id": session_id,
                "session": session,
                "welcome_message": welcome_msg
            }
        })
    except Exception as e:
        logger.error(f"create_session 错误: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get('/api/sessions/user/{user_id}')
async def get_session_by_user(user_id: str):
    """
    获取指定用户的最新会话。

    参数:
        user_id: 用户ID（路径参数）

    返回:
        JSONResponse: 包含最新会话信息，如果用户没有会话则返回 null
    """
    try:
        session = chat_mgr.get_session_by_user(user_id)
        if not session:
            return JSONResponse({
                "success": False,
                "data": None
            })

        return JSONResponse({
            "success": True,
            "data": session
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get('/api/sessions/{session_id}')
async def get_session(session_id: int):
    """
    获取指定会话详情。

    参数:
        session_id: 会话ID（路径参数）

    返回:
        JSONResponse: 包含会话信息和消息历史
    """
    try:
        session = chat_mgr.get_session_by_id(session_id)
        if not session:
            return JSONResponse({
                "success": False,
                "error": "会话不存在"
            }, status_code=404)

        return JSONResponse({
            "success": True,
            "data": session
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.delete('/api/sessions/{session_id}')
async def delete_session(session_id: int):
    """
    删除指定会话及其所有消息。

    参数:
        session_id: 会话ID（路径参数）

    返回:
        JSONResponse: 删除结果
    """
    try:
        success = chat_mgr.delete_session(session_id)
        if not success:
            return JSONResponse({
                "success": False,
                "error": "会话不存在"
            }, status_code=404)

        return JSONResponse({
            "success": True,
            "message": "会话已删除"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post('/api/sessions/{session_id}/messages')
async def send_message(session_id: int, request: Request):
    """
    发送消息并获取 AI 回复。

    请求体:
        {
            "message": "我的俯卧撑正确率不高，怎么改进？",  // 必填：用户消息
            "model": "Qwen"                              // 可选：指定模型
        }

    处理流程:
        1. 验证会话存在
        2. 如果是第一条消息，生成会话标题
        3. 添加用户消息到历史
        4. 调用 AI 模型生成回复
        5. 添加 AI 回复到历史

    返回:
        JSONResponse: {
            "success": true,
            "data": {
                "session": {...},
                "response": "同学你好！..."
            }
        }
    """
    try:
        session = chat_mgr.get_session_by_id(session_id)
        if not session:
            logger.warning(f"send_message: 会话 {session_id} 不存在")
            return JSONResponse({
                "success": False,
                "error": "会话不存在"
            }, status_code=404)

        data = await request.json()
        user_message = data.get('message')
        model_name = data.get('model')  # 允许前端指定模型

        if not user_message:
            logger.warning(f"send_message: 会话 {session_id} 消息内容为空")
            return JSONResponse({
                "success": False,
                "error": "消息内容不能为空"
            }, status_code=400)

        # 如果没有指定模型，使用会话默认模型
        if not model_name:
            model_name = session.get('model', 'local')

        logger.info(f"send_message: session_id={session_id}, message_length={len(user_message)}")

        # 如果是第一条用户消息，更新会话标题
        user_messages = [m for m in session["messages"] if m["role"] == "user"]
        if len(user_messages) == 0:
            chat_mgr.update_session_title(session_id, user_message, model_name)

        # 添加用户消息到历史
        chat_mgr.add_message(session_id, "user", user_message, model_name)

        # 获取更新后的会话（包含新消息）
        updated_session = chat_mgr.get_session_by_id(session_id)

        # 调用 AI 模型生成回复
        logger.info(f"send_message: 调用模型生成回复...")
        response = model_predict(model_name, updated_session["messages"])
        logger.info(f"send_message: 生成回复完成，长度={len(response)}")

        # 添加 AI 回复到历史
        chat_mgr.add_message(session_id, "assistant", response, model_name)

        # 获取最终的会话
        final_session = chat_mgr.get_session_by_id(session_id)

        return JSONResponse({
            "success": True,
            "data": {
                "session": final_session,
                "response": response
            }
        })
    except Exception as e:
        logger.error(f"send_message 错误: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post('/api/sessions/{session_id}/clear')
async def clear_session(session_id: int):
    """
    清空会话的所有消息（保留会话本身）。

    参数:
        session_id: 会话ID（路径参数）

    返回:
        JSONResponse: 清空结果
    """
    try:
        session = chat_mgr.get_session_by_id(session_id)
        if not session:
            return JSONResponse({
                "success": False,
                "error": "会话不存在"
            }, status_code=404)

        success = chat_mgr.clear_session_messages(session_id)
        if not success:
            return JSONResponse({
                "success": False,
                "error": "清空会话失败"
            }, status_code=500)

        return JSONResponse({
            "success": True,
            "message": "会话已清空"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get('/api/sessions/{session_id}/export')
async def export_session(session_id: int):
    """
    导出会话为 Markdown 文件。

    参数:
        session_id: 会话ID（路径参数）

    返回:
        FileResponse: Markdown 文件下载
    """
    try:
        temp_path = export_markdown(session_id, chat_mgr)
        if not temp_path:
            return JSONResponse({
                "success": False,
                "error": "会话不存在"
            }, status_code=404)

        return FileResponse(temp_path, filename=f"会话_{session_id}.md")
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get('/api/models')
async def list_models():
    """
    获取当前使用的本地模型信息。

    返回:
        JSONResponse: {
            "success": true,
            "data": {
                "model": "local",
                "model_path": "./models/Qwen2.5-7B-PE-Sports",
                "is_finetuned": true,
                "quantization": "4-bit"
            }
        }
    """
    try:
        import os
        from chat_module import FINETUNED_MODEL_PATH, BASE_MODEL_PATH, LOAD_IN_4BIT, LOAD_IN_8BIT, MODEL_PATH

        is_finetuned = os.path.exists(FINETUNED_MODEL_PATH)
        quantization = "4-bit" if LOAD_IN_4BIT else ("8-bit" if LOAD_IN_8BIT else "fp16")

        return JSONResponse({
            "success": True,
            "data": {
                "model": "local",
                "model_path": MODEL_PATH,
                "is_finetuned": is_finetuned,
                "base_model": BASE_MODEL_PATH,
                "quantization": quantization
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


# ================= AI 分析报告 API =================

@app.post('/api/analysis/generate')
async def api_generate_analysis_report(request: Request):
    """
    生成智能分析报告。

    支持两种分析类型：
    1. homework_feedback: 作业反馈分析
       - 需要 homework_id 和 student_id
       - 分析学生的作业表现，提供改进建议

    2. personalized_tips: 个性化训练建议
       - 需要 student_id
       - 基于历史数据提供长期训练规划

    请求体示例:
        {
            "student_id": "stu001",
            "homework_id": "hw001",           // 作业反馈必填
            "analysis_type": "homework_feedback",
            "query": "分析我的深蹲表现",
            "student_info": {"height": 175, "weight": 65}  // 可选
        }
    """
    return await generate_analysis_report(model_predict, request)


@app.get('/api/analysis/query')
async def api_query_analysis_report(request: Request):
    """
    查询已生成的 AI 分析报告。

    查询参数:
        - student_id: 学生ID（必填）
        - homework_id: 作业ID（可选）
        - analysis_type: 分析类型（可选）
    """
    return await query_analysis_report(request)


@app.get('/api/analysis/recent')
async def api_get_recent_analyses(request: Request):
    """
    获取最近的 AI 分析记录。

    查询参数:
        - student_id: 学生ID（可选，不填则返回所有）
        - limit: 返回数量限制（默认 10）
    """
    return await get_recent_analyses(request)


# ================= 应用启动 =================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)