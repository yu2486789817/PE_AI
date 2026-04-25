"""
database.py - 运动反馈数据库模块

数据库设计：
- exercise_feedback: 运动动作识别结果表

数据库文件：exercise_feedback.db（SQLite）
"""

import sqlite3
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime

# ================= 路径配置 =================
# 获取当前脚本所在目录，确保无论在哪里运行都使用正确的路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "exercise_feedback.db")


def init_database():
    """
    初始化数据库，创建 exercise_feedback 表。

    表结构设计：

    exercise_feedback 表 - 运动动作识别结果
        - id: 自增主键
        - homework_id: 作业ID（关联 MySQL homework 表）
        - student_id: 学生ID（关联 MySQL student 表）
        - pose_type: 动作类型（pushup/squat/deadlift）
        - uploaded_at: 上传时间
        - original_video_path: 原始视频路径
        - processed_video_path: 处理后视频存储路径
        - total_count: 总动作次数
        - correct_count: 正确动作次数
        - incorrect_count: 错误动作次数
        - feedback_json: 详细反馈数据（JSON 格式）
        - video_duration: 视频时长（秒）

    索引设计：
        - idx_homework_student: 按作业ID和学生ID联合索引
        - idx_student: 按学生ID索引（用于 AIChat 查询历史数据）
        - idx_upload_time: 按上传时间索引
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            homework_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            pose_type TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            original_video_path TEXT,
            processed_video_path TEXT NOT NULL,
            total_count INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            incorrect_count INTEGER DEFAULT 0,
            feedback_json TEXT,
            video_duration REAL,
            UNIQUE (homework_id, student_id, pose_type)
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_homework_student ON exercise_feedback (homework_id, student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_student ON exercise_feedback (student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_upload_time ON exercise_feedback (uploaded_at)")

    conn.commit()
    conn.close()


def insert_exercise_feedback(
    homework_id: str,
    student_id: str,
    pose_type: str,
    processed_video_path: str,
    total_count: int = 0,
    correct_count: int = 0,
    incorrect_count: int = 0,
    feedback_json: Optional[str] = None,
    video_duration: Optional[float] = None,
    original_video_path: Optional[str] = None
) -> int:
    """
    插入或更新一条健身动作分析反馈记录。

    如果记录已存在（相同 homework_id + student_id + pose_type），
    则更新现有记录；否则插入新记录。

    参数:
        homework_id: 作业ID
        student_id: 学生ID
        pose_type: 动作类型（pushup/squat/deadlift）
        processed_video_path: 处理后视频存储路径
        total_count: 总动作次数
        correct_count: 正确动作次数
        incorrect_count: 错误动作次数
        feedback_json: 详细反馈数据（JSON 格式字符串）
        video_duration: 视频时长（秒）
        original_video_path: 原始视频路径

    返回:
        int: 记录的 ID
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    local_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")

    # 检查记录是否已存在
    cursor.execute("""
        SELECT id FROM exercise_feedback
        WHERE homework_id = ? AND student_id = ? AND pose_type = ?
    """, (homework_id, student_id, pose_type))

    existing_record = cursor.fetchone()

    if existing_record:
        # 更新现有记录
        record_id = existing_record[0]
        cursor.execute("""
            UPDATE exercise_feedback SET
                uploaded_at = ?,
                original_video_path = ?,
                processed_video_path = ?,
                total_count = ?,
                correct_count = ?,
                incorrect_count = ?,
                feedback_json = ?,
                video_duration = ?
            WHERE id = ?
        """, (
            local_time, original_video_path, processed_video_path,
            total_count, correct_count, incorrect_count,
            feedback_json, video_duration,
            record_id
        ))
    else:
        # 插入新记录
        cursor.execute("""
            INSERT INTO exercise_feedback (
                homework_id, student_id, pose_type, uploaded_at, original_video_path,
                processed_video_path, total_count, correct_count, incorrect_count,
                feedback_json, video_duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            homework_id, student_id, pose_type, local_time, original_video_path,
            processed_video_path, total_count, correct_count, incorrect_count,
            feedback_json, video_duration
        ))
        record_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return record_id


def update_exercise_feedback(
    record_id: int,
    total_count: Optional[int] = None,
    correct_count: Optional[int] = None,
    incorrect_count: Optional[int] = None,
    feedback_json: Optional[str] = None,
    video_duration: Optional[float] = None
) -> bool:
    """
    更新健身动作分析反馈记录。

    参数:
        record_id: 记录ID
        total_count: 总动作次数
        correct_count: 正确动作次数
        incorrect_count: 错误动作次数
        feedback_json: 详细反馈数据
        video_duration: 视频时长

    返回:
        bool: 更新是否成功
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updates = []
    params = []

    if total_count is not None:
        updates.append("total_count = ?")
        params.append(total_count)

    if correct_count is not None:
        updates.append("correct_count = ?")
        params.append(correct_count)

    if incorrect_count is not None:
        updates.append("incorrect_count = ?")
        params.append(incorrect_count)

    if feedback_json is not None:
        updates.append("feedback_json = ?")
        params.append(feedback_json)

    if video_duration is not None:
        updates.append("video_duration = ?")
        params.append(video_duration)

    if not updates:
        conn.close()
        return False

    params.append(record_id)
    update_sql = f"UPDATE exercise_feedback SET {', '.join(updates)} WHERE id = ?"

    cursor.execute(update_sql, params)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    return success


def get_exercise_feedback(homework_id: str, student_id: str, pose_type: str) -> Optional[Dict[str, Any]]:
    """
    根据作业ID、学生ID和动作类型查询反馈记录。

    参数:
        homework_id: 作业ID
        student_id: 学生ID
        pose_type: 动作类型

    返回:
        dict: 反馈记录信息，如果不存在则返回 None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM exercise_feedback
        WHERE homework_id = ? AND student_id = ? AND pose_type = ?
    """, (homework_id, student_id, pose_type))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def get_exercise_feedback_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """
    根据记录ID查询反馈记录。

    参数:
        record_id: 记录ID

    返回:
        dict: 反馈记录信息，如果不存在则返回 None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM exercise_feedback WHERE id = ?", (record_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def get_student_all_records(student_id: str) -> list:
    """
    获取指定学生的所有运动记录。

    用于 AIChat 服务获取学生历史数据生成个性化报告。

    参数:
        student_id: 学生ID

    返回:
        list: 所有运动记录列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM exercise_feedback
        WHERE student_id = ?
        ORDER BY uploaded_at DESC
    """, (student_id,))

    rows = cursor.fetchall()
    conn.close()

    records = []
    for row in rows:
        record = dict(row)
        # 解析 JSON 字段
        if record.get('feedback_json'):
            try:
                record['feedback_data'] = json.loads(record['feedback_json'])
            except json.JSONDecodeError:
                record['feedback_data'] = {}
        else:
            record['feedback_data'] = {}
        records.append(record)

    return records


def get_records_by_homework_student(homework_id: str, student_id: str) -> list:
    """
    获取指定作业和学生的所有运动记录。

    参数:
        homework_id: 作业ID
        student_id: 学生ID

    返回:
        list: 运动记录列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM exercise_feedback
        WHERE homework_id = ? AND student_id = ?
        ORDER BY uploaded_at DESC
    """, (homework_id, student_id))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_all_records() -> list:
    """
    获取所有运动记录。

    返回:
        list: 所有运动记录列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM exercise_feedback ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
