"""
database.py - AI 聊天数据库模块

数据库设计：
- sessions: 会话元信息表
- messages: 消息历史表
- ai_analysis_reports: AI 分析报告表

数据库文件：chat_history.db（SQLite）
"""

import sqlite3
import os

# ================= 路径配置 =================
# 获取当前脚本所在目录，确保无论在哪里运行都使用正确的路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "chat_history.db")


def get_db_path():
    """获取数据库路径，供其他模块使用。"""
    return DB_PATH


def init_db():
    """
    初始化数据库，创建所有表。

    表结构设计：

    1. sessions 表 - 会话元信息
       - id: 自增主键
       - user_id: 用户ID（关联 MySQL 用户表）
       - title: 会话标题
       - model: 使用的模型（固定为 local）
       - role: 用户角色（student/teacher）
       - created_at: 创建时间
       - updated_at: 更新时间

    2. messages 表 - 消息历史
       - id: 自增主键
       - session_id: 所属会话ID（外键）
       - role: 消息角色（user/assistant/system）
       - content: 消息内容
       - model: 使用的模型
       - timestamp: 时间戳

    3. ai_analysis_reports 表 - AI 分析报告
       - id: 自增主键
       - homework_id: 作业ID
       - student_id: 学生ID
       - pose_type: 动作类型
       - analysis_type: 分析类型
       - query_content: 用户查询
       - report_content: AI 生成的报告
       - raw_data: 原始数据（JSON，从 Yolo_backend 获取的副本）
       - model_used: 使用的模型
       - student_info: 学生个人信息（JSON）
       - created_at/updated_at: 时间戳
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ========== 创建会话表 ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            model TEXT DEFAULT 'local',
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ========== 创建消息表 ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            model TEXT DEFAULT 'local',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    ''')

    # ========== 创建 AI 分析报告表 ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_analysis_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            homework_id TEXT,
            student_id TEXT NOT NULL,
            pose_type TEXT,
            analysis_type TEXT NOT NULL,
            query_content TEXT,
            report_content TEXT NOT NULL,
            raw_data TEXT,
            model_used TEXT DEFAULT 'local',
            student_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(homework_id, student_id, analysis_type)
        )
    ''')

    # ========== 创建索引 ==========
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages (session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_student ON ai_analysis_reports (student_id)")

    conn.commit()
    conn.close()
