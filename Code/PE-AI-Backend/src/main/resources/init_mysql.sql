-- ============================================================
-- PE AI 智慧运动课堂 - MySQL 建表脚本
-- 数据库: se_project
-- ============================================================
DROP DATABASE IF EXISTS se_project;
CREATE DATABASE se_project DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE se_project;
SET NAMES utf8mb4;

-- -------------------------------------------------------
-- 基准教师表 (std_teacher) - 注册前必须存在
-- -------------------------------------------------------
DROP TABLE IF EXISTS std_teacher;
CREATE TABLE std_teacher (
    id          VARCHAR(20) PRIMARY KEY COMMENT '教师工号',
    name        VARCHAR(50) NOT NULL COMMENT '教师姓名'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='基准教师表';

-- -------------------------------------------------------
-- 基准学生表 (std_student) - 注册前必须存在
-- -------------------------------------------------------
DROP TABLE IF EXISTS std_student;
CREATE TABLE std_student (
    id          VARCHAR(20) PRIMARY KEY COMMENT '学生学号',
    name        VARCHAR(50) NOT NULL COMMENT '学生姓名'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='基准学生表';

-- -------------------------------------------------------
-- 教师用户表 (teacher)
-- -------------------------------------------------------
DROP TABLE IF EXISTS teacher;
CREATE TABLE teacher (
    id              VARCHAR(20) PRIMARY KEY COMMENT '教师工号',
    password        VARCHAR(64) NOT NULL COMMENT 'SHA-256密码',
    name            VARCHAR(50) NOT NULL COMMENT '姓名',
    gender          VARCHAR(10) COMMENT '性别',
    title           VARCHAR(50) COMMENT '职称',
    college         VARCHAR(100) COMMENT '学院',
    department      VARCHAR(100) COMMENT '系',
    login_time     DATETIME DEFAULT NULL COMMENT '最后登录时间',
    created_time    DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师用户表';

-- -------------------------------------------------------
-- 学生用户表 (student)
-- -------------------------------------------------------
DROP TABLE IF EXISTS student;
CREATE TABLE student (
    id              VARCHAR(20) PRIMARY KEY COMMENT '学生学号',
    password        VARCHAR(64) NOT NULL COMMENT 'SHA-256密码',
    name            VARCHAR(50) NOT NULL COMMENT '姓名',
    gender          VARCHAR(10) COMMENT '性别',
    college         VARCHAR(100) COMMENT '学院',
    department      VARCHAR(100) COMMENT '系',
    major           VARCHAR(100) COMMENT '专业',
    login_time     DATETIME DEFAULT NULL COMMENT '最后登录时间',
    created_time    DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生用户表';

-- -------------------------------------------------------
-- 课程表 (course)
-- -------------------------------------------------------
DROP TABLE IF EXISTS course;
CREATE TABLE course (
    id              VARCHAR(20) PRIMARY KEY COMMENT '课程ID',
    teacher_id      VARCHAR(20) NOT NULL COMMENT '授课教师工号',
    name            VARCHAR(100) NOT NULL COMMENT '课程名称',
    info            TEXT COMMENT '课程描述',
    code            VARCHAR(20) NOT NULL COMMENT '课程码(学生加入用)',
    semester        INT DEFAULT 1 COMMENT '学期',
    is_active       TINYINT DEFAULT 1 COMMENT '是否激活 1=是 0=否',
    created_time    DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程表';

-- -------------------------------------------------------
-- 学生选课关联表 (student_course)
-- -------------------------------------------------------
DROP TABLE IF EXISTS student_course;
CREATE TABLE student_course (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  VARCHAR(20) NOT NULL COMMENT '学生学号',
    course_id   VARCHAR(20) NOT NULL COMMENT '课程ID',
    joined_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    UNIQUE KEY uk_student_course (student_id, course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生选课关联表';

-- -------------------------------------------------------
-- 作业表 (homework)
-- -------------------------------------------------------
DROP TABLE IF EXISTS homework;
CREATE TABLE homework (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    course_id       VARCHAR(20) NOT NULL COMMENT '课程ID',
    title           VARCHAR(200) NOT NULL COMMENT '作业标题',
    description     TEXT COMMENT '作业描述',
    deadline        DATETIME COMMENT '截止时间',
    create_time     DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='作业表';

-- -------------------------------------------------------
-- AI动作类型配置表 (ai_type)
-- -------------------------------------------------------
DROP TABLE IF EXISTS ai_type;
CREATE TABLE ai_type (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    homework_id     INT NOT NULL COMMENT '作业ID',
    type            VARCHAR(50) COMMENT '动作类型 如squat/pushup',
    num             INT DEFAULT 0 COMMENT '标准次数'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI动作类型配置表';

-- -------------------------------------------------------
-- 作业提交记录表 (submit)
-- -------------------------------------------------------
DROP TABLE IF EXISTS submit;
CREATE TABLE submit (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    homework_id         INT NOT NULL COMMENT '作业ID',
    student_id          VARCHAR(20) NOT NULL COMMENT '学生学号',
    video_url          VARCHAR(500) COMMENT '视频URL',
    score              INT COMMENT '得分',
    ai_feedback        TEXT COMMENT 'AI反馈',
    teacher_feedback   TEXT COMMENT '教师反馈',
    create_time        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='作业提交记录表';

-- -------------------------------------------------------
-- 教学视频表 (class)
-- -------------------------------------------------------
DROP TABLE IF EXISTS class;
CREATE TABLE class (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    course_id       VARCHAR(20) NOT NULL COMMENT '课程ID',
    title           VARCHAR(200) NOT NULL COMMENT '视频标题',
    description     TEXT COMMENT '视频描述',
    content_url     VARCHAR(500) COMMENT '视频URL',
    create_time     DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教学视频表';

-- -------------------------------------------------------
-- 外键约束 (可选, 如需严格参照完整性可取消注释)
-- -------------------------------------------------------
-- ALTER TABLE course ADD CONSTRAINT fk_course_teacher FOREIGN KEY (teacher_id) REFERENCES teacher(id);
-- ALTER TABLE student_course ADD CONSTRAINT fk_sc_student FOREIGN KEY (student_id) REFERENCES student(id);
-- ALTER TABLE student_course ADD CONSTRAINT fk_sc_course FOREIGN KEY (course_id) REFERENCES course(id);
-- ALTER TABLE homework ADD CONSTRAINT fk_hw_course FOREIGN KEY (course_id) REFERENCES course(id);
-- ALTER TABLE ai_type ADD CONSTRAINT fk_at_homework FOREIGN KEY (homework_id) REFERENCES homework(id);
-- ALTER TABLE submit ADD CONSTRAINT fk_submit_homework FOREIGN KEY (homework_id) REFERENCES homework(id);
-- ALTER TABLE submit ADD CONSTRAINT fk_submit_student FOREIGN KEY (student_id) REFERENCES student(id);
-- ALTER TABLE class ADD CONSTRAINT fk_class_course FOREIGN KEY (course_id) REFERENCES course(id);
