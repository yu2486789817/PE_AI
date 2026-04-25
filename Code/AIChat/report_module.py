"""
report_module.py - AI 分析报告生成模块

功能：
1. 作业反馈分析：分析单次作业的表现
2. 个性化训练建议：基于历史数据提供长期规划

数据流程：
1. 前端请求 → generate_analysis_report()
2. 调用 Yolo_backend API 获取运动数据
   - homework_feedback: GET /get_record_details?homework_id=xxx&student_id=xxx
   - personalized_tips: GET /api/student/all-records/{student_id}
3. 构造 AI Prompt → model_predict() (本地模型)
4. 保存报告到 chat_history.db
5. 返回结果给前端

数据库交互：
- Yolo_backend: exercise_feedback.db (只读，通过 API 访问)
- AIChat: chat_history.db (读写，存储报告)
"""

import os
import requests
import json
import sqlite3
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from database import DB_PATH  # 导入数据库路径

# ================= 日志配置 =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================= 配置 =================
YOLO_BASE_URL = os.getenv("YOLO_BASE_URL", "http://localhost:8000")

# ================= AI 分析提示词模板 =================
AI_PROMPTS = {
    "homework_feedback": """你是体育教练，根据数据给出评价和建议（120字内）。
数据：{student_data}
要求：指出主要错误，给出改进方法。""",

    "personalized_tips": """你是体育教练，根据数据给出训练建议（120字内）。
信息：{student_info}
数据：{student_data}
要求：分析问题，给出建议。"""
}


def _parse_feedback_json(data):
    """
    解析数据中的 feedback_json 字段，将 JSON 字符串转为字典。

    解决双重 JSON 编码导致中文显示为 Unicode 的问题。
    """
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'feedback_json' in item:
                try:
                    item['feedback_json'] = json.loads(item['feedback_json'])
                except (json.JSONDecodeError, TypeError):
                    pass
    return data


def _summarize_exercise_data(records):
    """
    将运动记录精简为摘要，只保留关键信息。
    """
    if not records:
        return []

    summary = []
    for record in records:
        total = record.get("total_count", 0)
        correct = record.get("correct_count", 0)
        incorrect = record.get("incorrect_count", 0)
        accuracy = round(correct / total * 100, 1) if total > 0 else 0

        # 提取错误统计
        feedback = record.get("feedback_json", {})
        error_summary = {}
        if isinstance(feedback, dict):
            error_summary = feedback.get("error_summary", {})

        logger.info(f"记录: total={total}, correct={correct}, errors={error_summary}")

        item = {
            "动作": record.get("pose_type", "未知"),
            "次数": total,
            "正确": correct,
            "错误": incorrect,
            "正确率": f"{accuracy}%",
        }
        if error_summary:
            item["错误"] = error_summary

        summary.append(item)

    return summary


# ================= Yolo_backend 数据获取 =================

def get_yolo_records_by_homework_student(homework_id: str, student_id: str) -> list:
    """
    获取指定作业和学生的运动记录详情。

    调用 Yolo_backend 接口: GET /get_record_details?homework_id=xxx&student_id=xxx

    参数:
        homework_id: 作业ID
        student_id: 学生ID

    返回:
        list: 记录详情列表，失败返回 None
    """
    url = f"{YOLO_BASE_URL}/get_record_details"
    params = {"homework_id": homework_id, "student_id": student_id}

    try:
        logger.info(f"调用 Yolo_backend: /get_record_details?homework_id={homework_id}&student_id={student_id}")
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"获取记录成功，共 {len(data) if isinstance(data, list) else 1} 条")
            return data
        logger.warning(f"Yolo_backend 返回状态码: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"调用 Yolo_backend 接口失败: {e}")
        return None


def get_yolo_student_all_records(student_id: str) -> list:
    """
    获取学生的所有运动记录。

    调用 Yolo_backend 接口: GET /api/student/all-records/{student_id}

    参数:
        student_id: 学生ID

    返回:
        list: 所有运动记录列表，失败返回 None
    """
    url = f"{YOLO_BASE_URL}/api/student/all-records/{student_id}"

    try:
        logger.info(f"调用 Yolo_backend: /api/student/all-records/{student_id}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"获取学生 {student_id} 所有记录成功，共 {len(data)} 条")
            return data
        logger.warning(f"Yolo_backend 返回状态码: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"调用 Yolo_backend 接口失败: {e}")
        return None


# ================= 报告数据库操作 =================

def save_ai_analysis_report(
    homework_id: str,
    student_id: str,
    pose_type: str,
    analysis_type: str,
    query_content: str,
    report_content: str,
    raw_data: str,
    model_used: str,
    student_info: dict = None
) -> int:
    """
    保存 AI 分析报告到数据库。

    返回:
        int: 报告 ID
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO ai_analysis_reports
        (homework_id, student_id, pose_type, analysis_type, query_content,
         report_content, raw_data, model_used, student_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        homework_id, student_id, pose_type, analysis_type, query_content,
        report_content, raw_data, model_used,
        json.dumps(student_info, ensure_ascii=False) if student_info else None
    ))

    conn.commit()
    report_id = cursor.lastrowid
    conn.close()

    return report_id


def get_ai_analysis_report(homework_id: str, student_id: str, analysis_type: str = None) -> list:
    """
    查询 AI 分析报告。

    返回:
        list: 报告列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if analysis_type:
        if homework_id:
            cursor.execute('''
                SELECT * FROM ai_analysis_reports
                WHERE homework_id = ? AND student_id = ? AND analysis_type = ?
                ORDER BY created_at DESC
            ''', (homework_id, student_id, analysis_type))
        else:
            cursor.execute('''
                SELECT * FROM ai_analysis_reports
                WHERE student_id = ? AND analysis_type = ?
                ORDER BY created_at DESC
            ''', (student_id, analysis_type))
    else:
        if homework_id:
            cursor.execute('''
                SELECT * FROM ai_analysis_reports
                WHERE homework_id = ? AND student_id = ?
                ORDER BY created_at DESC
            ''', (homework_id, student_id))
        else:
            cursor.execute('''
                SELECT * FROM ai_analysis_reports
                WHERE student_id = ?
                ORDER BY created_at DESC
            ''', (student_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ================= API 接口 =================

async def generate_analysis_report(model_predict_func, request: Request):
    """
    生成智能分析报告。

    支持两种分析类型：
    1. homework_feedback: 作业反馈分析
    2. personalized_tips: 个性化训练建议
    """
    import time
    start_time = time.time()

    try:
        data = await request.json()
        homework_id = data.get('homework_id')
        student_id = data.get('student_id')
        analysis_type = data.get('analysis_type', 'homework_feedback')
        query_content = data.get('query', '')
        student_info = data.get('student_info', {})

        if not student_id:
            return JSONResponse({"success": False, "error": "学生ID不能为空"}, status_code=400)

        if analysis_type not in AI_PROMPTS:
            return JSONResponse({"success": False, "error": f"不支持的分析类型: {analysis_type}"}, status_code=400)

        # ========== 获取运动数据 ==========
        t1 = time.time()
        if analysis_type == "homework_feedback":
            if not homework_id:
                return JSONResponse({"success": False, "error": "作业反馈类型需要提供作业ID"}, status_code=400)

            yolo_data = get_yolo_records_by_homework_student(homework_id, student_id)
            if not yolo_data:
                return JSONResponse({"success": False, "error": "未能从 Yolo_backend 获取作业数据"}, status_code=500)

            # 解析并精简数据
            yolo_data = _parse_feedback_json(yolo_data)
            summary_data = _summarize_exercise_data(yolo_data)

            prompt = AI_PROMPTS[analysis_type].format(
                student_data=json.dumps(summary_data, ensure_ascii=False)
            )
            raw_data = json.dumps(summary_data, ensure_ascii=False)
            pose_type = yolo_data[0].get('pose_type', '') if isinstance(yolo_data, list) and yolo_data else ''

        else:  # personalized_tips
            yolo_data = get_yolo_student_all_records(student_id)
            if not yolo_data:
                return JSONResponse({"success": False, "error": "未能从 Yolo_backend 获取学生历史数据"}, status_code=500)

            # 解析并精简数据
            yolo_data = _parse_feedback_json(yolo_data)
            summary_data = _summarize_exercise_data(yolo_data)

            prompt = AI_PROMPTS[analysis_type].format(
                student_info=json.dumps(student_info, ensure_ascii=False),
                student_data=json.dumps(summary_data, ensure_ascii=False)
            )
            raw_data = json.dumps(summary_data, ensure_ascii=False)
            pose_type = ''

        t2 = time.time()
        logger.info(f"[性能] 数据获取和处理耗时: {t2-t1:.2f}s")

        # ========== 调用本地模型生成报告 ==========
        # 直接发送 prompt，不添加额外的 system message
        messages = [{"role": "user", "content": prompt}]

        t3 = time.time()
        report_content = model_predict_func("local", messages)
        t4 = time.time()
        logger.info(f"[性能] 模型推理耗时: {t4-t3:.2f}s")

        # 保存报告
        save_ai_analysis_report(
            homework_id, student_id, pose_type, analysis_type,
            query_content, report_content, raw_data, "local", student_info
        )

        total_time = time.time() - start_time
        logger.info(f"[性能] 报告生成总耗时: {total_time:.2f}s")

        return JSONResponse({
            "success": True,
            "data": {"report": report_content, "analysis_type": analysis_type}
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def query_analysis_report(request: Request):
    """查询已生成的 AI 分析报告。"""
    try:
        homework_id = request.query_params.get('homework_id')
        student_id = request.query_params.get('student_id')
        analysis_type = request.query_params.get('analysis_type')

        if not student_id:
            return JSONResponse({"success": False, "error": "学生ID不能为空"}, status_code=400)

        reports = get_ai_analysis_report(homework_id, student_id, analysis_type)

        return JSONResponse({"success": True, "data": reports})

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def get_recent_analyses(request: Request):
    """获取最近的 AI 分析记录。"""
    try:
        student_id = request.query_params.get('student_id')
        limit = int(request.query_params.get('limit', 10))

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if student_id:
            cursor.execute('''
                SELECT * FROM ai_analysis_reports
                WHERE student_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (student_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM ai_analysis_reports
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return JSONResponse({"success": True, "data": [dict(row) for row in rows]})

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
