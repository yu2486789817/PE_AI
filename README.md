# PE AI Manager - 大学体育智能课堂平台

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Spring Boot](https://img.shields.io/badge/Backend-Spring%20Boot%203-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Vue](https://img.shields.io/badge/Frontend-Vue%203-4fc08d.svg)](https://vuejs.org/)
[![Uni-App](https://img.shields.io/badge/Mobile-Uni--App-2b9939.svg)](https://uniapp.dcloud.net.cn/)
[![Python](https://img.shields.io/badge/AI-Python%20%7C%20YOLO-blue.svg)](https://www.python.org/)

## 📝 项目简介 (Project Overview)

**PE AI Manager (大学体育智能课堂平台)** 是一款面向高校体育教学的现代化管理与辅助系统。针对传统体育教学中课外指导缺失、视频作业批改繁重等痛点，本项目利用 AI 视觉分析技术（YOLO）与智能化管理手段，为师生提供了一个高效、互动的智慧教学平台。

**PE AI Manager** is a modern intelligent classroom platform designed for university physical education. It addresses the lack of personalized feedback and the heavy workload of manual video grading by leveraging AI video analysis (YOLO) to provide automated feedback, real-time posture correction, and streamlined course management.

---

## ✨ 核心功能 (Core Features)

- 🤖 **AI 动作分析**: 基于 YOLO 的视频流分析，自动评估投篮、仰卧起坐等体育动作，提供关节角度分析与专业建议。
- 📊 **课程与作业管理**: 完整的教师端后台，支持在线布置作业、自动批改统计与学生进度追踪。
- 📱 **多端覆盖**: 专为学生设计的 Uni-app 移动端应用，支持视频录制、即时反馈查看与 AI 助教交互。
- 💬 **智能 AI 助教**: 集成 LLM 的智能助手，随时为师生解答体育知识、动作规范及系统操作问题。
- 📈 **数据驱动教学**: 自动生成学生运动报告，帮助教师精准掌握教学效果，实施差异化指导。

---

## 🏗️ 项目架构 (Architecture)

项目采用前后端分离及微服务化思想构建，涵盖了从底层 AI 模型到高层业务逻辑的完整链路：

```text
PE-AI-Project/
├── Code/
│   ├── PE-AI-Backend/          # [Java/Spring Boot] 核心业务逻辑后台
│   ├── PE_AI_Manager_Frontend/ # [Vue 3/Vite] 教师/管理员管理 Web 端
│   ├── PE_AI_Student_UniApp/   # [Vue/Uni-app] 学生移动端应用
│   ├── Yolo_backend/           # [Python/FastAPI] AI 视频处理与推理微服务
│   ├── AIChat/                 # AI 助手前端及交互逻辑
│   ├── sql/                    # 数据库初始化与迁移脚本
│   └── 测试数据生成/             # 自动化测试与 Mock 数据脚本
└── Docs/                       # 项目需求文档 (SRS/SDD)、PPT 及 POS
```

---

## 🛠️ 技术栈 (Tech Stack)

### 后端 (Backend)
- **Framework**: Spring Boot 3.x, MyBatis Plus
- **Database**: MySQL 8.x, Redis
- **Communication**: RESTful API, WebSocket (for real-time AI feedback)

### 前端 (Frontend)
- **Web**: Vue 3, Element Plus, Tailwind CSS
- **Mobile**: Uni-app (Vue 3 version), GraceUI/Tailwind
- **State Management**: Pinia

### AI & 视觉 (AI & CV)
- **Language**: Python 3.9+
- **Framework**: PyTorch, Ultralytics (YOLOv8)
- **Processing**: OpenCV, Mediapipe

---

## 🚀 快速开始 (Quick Start)

> 详细的子模块启动指南请参考各目录下对应的 `README.md`。

1. **环境准备**:
   - 安装 JDK 17+, Maven, Node.js 18+, Python 3.9+
   - 配置 MySQL 数据库并导入 `Code/sql` 中的脚本。
2. **启动 AI 微服务**:
   ```bash
   cd Code/Yolo_backend
   pip install -r requirements.txt
   python main.py
   ```
3. **启动后端服务**:
   ```bash
   cd Code/PE-AI-Backend
   mvn spring-boot:run
   ```
4. **启动管理端**:
   ```bash
   cd Code/PE_AI_Manager_Frontend
   npm install
   npm run dev
   ```

---

## 📄 开源协议 (License)

本项目遵循 [MIT License](LICENSE) 开源协议。

© 2026 PE-AI Project Team. All Rights Reserved.
