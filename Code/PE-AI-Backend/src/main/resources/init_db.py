import pymysql
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_FILES = ['init_mysql.sql', 'data_import.sql', 'seed_data_utf8.sql']

conn = pymysql.connect(
    host='localhost', port=3306,
    user='root', password='YUSHU750705',
    charset='utf8mb4'
)

cursor = conn.cursor()
cursor.execute("DROP DATABASE IF EXISTS se_project")
cursor.execute("CREATE DATABASE se_project CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.execute("USE se_project")
cursor.close()
print("[OK] Database recreated")

for sql_file in SQL_FILES:
    path = os.path.join(SCRIPT_DIR, sql_file)
    if not os.path.exists(path):
        print(f"[SKIP] {sql_file} not found")
        continue

    with open(path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    sql_content = re.sub(r'^\s*USE\s+se_project\s*;?\s*$', '', sql_content, flags=re.MULTILINE)
    sql_content = re.sub(r'^\s*SET\s+NAMES\s+utf8mb4\s*;?\s*$', '', sql_content, flags=re.MULTILINE)
    sql_content = re.sub(r'^\s*DROP\s+DATABASE.*?;?\s*$', '', sql_content, flags=re.MULTILINE | re.IGNORECASE)
    sql_content = re.sub(r'^\s*CREATE\s+DATABASE.*?;?\s*$', '', sql_content, flags=re.MULTILINE | re.IGNORECASE)

    statements = [s.strip() for s in sql_content.split(';') if s.strip()]

    print(f"[EXEC] {sql_file} ({len(statements)} statements)")
    cursor = conn.cursor()
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except Exception as e:
            err_msg = str(e)[:100]
            if 'already exists' not in err_msg.lower() and 'duplicate' not in err_msg.lower():
                print(f"  [WARN] {err_msg}")
    conn.commit()
    cursor.close()
    print(f"  [OK] {sql_file} done")

cursor = conn.cursor()
cursor.execute("SELECT name FROM teacher WHERE id='94128'")
row = cursor.fetchone()
print(f"\n[VERIFY] teacher 94128 name = {row[0]}")

cursor.execute("SELECT name FROM course WHERE id='C001'")
row = cursor.fetchone()
print(f"[VERIFY] course C001 name = {row[0]}")

cursor.execute("""
    SELECT CONCAT('std_teacher: ', COUNT(*)) FROM std_teacher
    UNION ALL SELECT CONCAT('std_student: ', COUNT(*)) FROM std_student
    UNION ALL SELECT CONCAT('teacher: ', COUNT(*)) FROM teacher
    UNION ALL SELECT CONCAT('student: ', COUNT(*)) FROM student
    UNION ALL SELECT CONCAT('course: ', COUNT(*)) FROM course
    UNION ALL SELECT CONCAT('homework: ', COUNT(*)) FROM homework
    UNION ALL SELECT CONCAT('ai_type: ', COUNT(*)) FROM ai_type
    UNION ALL SELECT CONCAT('submit: ', COUNT(*)) FROM submit
    UNION ALL SELECT CONCAT('student_course: ', COUNT(*)) FROM student_course
""")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.close()
conn.close()
print("\n[DONE] 初始化完成！教师: 94128/123456  学生: 2359086/123456")
