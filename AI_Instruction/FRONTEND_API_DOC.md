# PE AI 前端 API 接口文档

本文档描述前端需要调用的所有后端 API 接口。

## 目录

- [服务概览](#服务概览)
- [Yolo_backend API (端口 8000)](#yolo_backend-api-端口-8000)
- [AIChat API (端口 5000)](#aichat-api-端口-5000)
- [错误处理](#错误处理)
- [调用示例](#调用示例)

---

## 服务概览

| 服务名称 | 端口 | 功能 | 前端调用场景 |
|---------|------|------|-------------|
| Yolo_backend | 8000 | 视频处理、动作识别 | 学生上传作业视频、查看处理结果 |
| AIChat | 5000 | AI 聊天、报告生成 | AI 助手对话、生成分析报告 |

**注意：** 生产环境中，前端通过 PE-AI-Backend (端口 5001) 代理调用这些服务。开发调试时可直接调用。

---

## Yolo_backend API (端口 8000)

### 1. 健康检查

```
GET /health
```

**响应示例：**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "active_sessions": 0
}
```

---

### 2. 获取支持的动作类型

```
GET /supported_poses
```

**响应示例：**
```json
{
  "supported_poses": ["pushup", "squat", "deadlift"]
}
```

**动作类型说明：**
| 类型 | 中文名称 | 关键点 |
|-----|---------|-------|
| pushup | 俯卧撑 | 右肩-右肘-右腕 |
| squat | 深蹲 | 右髋-右膝-右踝 |
| deadlift | 硬拉 | 右肩-右髋-右膝 |

---

### 3. 处理并保存视频（核心接口）

```
POST /process_and_save_video
```

**请求参数：**

| 参数 | 类型 | 位置 | 必填 | 说明 |
|-----|------|-----|-----|------|
| homework_id | string | Query | 是 | 作业ID |
| student_id | string | Query | 是 | 学生ID |
| pose_type | string | Query | 否 | 动作类型，默认 "pushup" |
| file | binary | Body | 是 | 视频文件 (multipart/form-data) |

**请求示例：**
```javascript
const formData = new FormData();
formData.append('file', videoFile);

const response = await fetch(
  'http://localhost:8000/process_and_save_video?homework_id=hw001&student_id=stu001&pose_type=pushup',
  {
    method: 'POST',
    body: formData
  }
);
```

**响应格式：SSE (Server-Sent Events) 流式响应**

前端需要使用 `EventSource` 或手动解析 SSE 流：

```javascript
// 使用 fetch 处理 SSE 流
const response = await fetch(url, { method: 'POST', body: formData });
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  // 解析 SSE 格式: "data: {...}\n\n"
  const lines = text.split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const jsonStr = line.slice(6);
      const event = JSON.parse(jsonStr);
      handleEvent(event);
    }
  }
}
```

**SSE 事件类型：**

#### 3.1 初始化事件 (init)
```json
{
  "event": "init",
  "data": {
    "message": "开始处理视频",
    "fps": 30,
    "width": 1920,
    "height": 1080,
    "frame_count": 360
  }
}
```

#### 3.2 帧处理事件 (frame) - 每5帧发送一次
```json
{
  "event": "frame",
  "data": {
    "frame_index": 50,
    "processed_frame_count": 10,
    "count": 3,
    "max_count": 3,
    "image": "base64编码的图像..."
  }
}
```

**前端展示：** 将 `image` 字段的 base64 字符串设置到 `<img>` 标签的 `src` 属性实现实时预览。

#### 3.3 最终统计事件 (final_stats)
```json
{
  "event": "final_stats",
  "data": {
    "message": "视频处理完成",
    "max_count": 12,
    "processed_frame_count": 180,
    "total_time": 12.0,
    "saved_path": "homework/hw001/stu001/processed_video.mp4",
    "video_url": "/get_processed_video?homework_id=hw001&student_id=stu001"
  }
}
```

#### 3.4 错误事件 (error)
```json
{
  "event": "error",
  "data": {
    "message": "错误描述"
  }
}
```

---

### 4. 获取处理后的视频

```
GET /get_processed_video
```

**请求参数：**

| 参数 | 类型 | 位置 | 必填 | 说明 |
|-----|------|-----|-----|------|
| homework_id | string | Query | 是 | 作业ID |
| student_id | string | Query | 是 | 学生ID |
| download | boolean | Query | 否 | 是否下载，默认 false |

**响应：**
- `download=false`：SSE 流式返回视频帧（用于预览）
- `download=true`：返回视频文件下载

**下载示例：**
```javascript
window.open('http://localhost:8000/get_processed_video?homework_id=hw001&student_id=stu001&download=true');
```

---

### 5. 查询运动记录

```
GET /query_records
```

**请求参数：**

| 参数 | 类型 | 位置 | 必填 | 说明 |
|-----|------|-----|-----|------|
| homework_id | string | Query | 是 | 作业ID |
| student_id | string | Query | 是 | 学生ID |
| pose_type | string | Query | 否 | 动作类型，不填则返回所有类型 |

**响应示例：**
```json
[
  {
    "id": 1,
    "homework_id": "hw001",
    "student_id": "stu001",
    "pose_type": "pushup",
    "uploaded_at": "2024-01-15 10:30:00",
    "processed_video_path": "homework/hw001/stu001/processed_video.mp4",
    "total_count": 12,
    "correct_count": 10,
    "incorrect_count": 2,
    "feedback_json": "{\"events\": [...], \"performance\": {...}}",
    "video_duration": 12.5
  }
]
```

**字段说明：**
| 字段 | 说明 |
|-----|------|
| total_count | 总动作次数 |
| correct_count | 正确次数 |
| incorrect_count | 错误次数 |
| feedback_json | 详细反馈数据（JSON字符串） |
| video_duration | 视频时长（秒） |

---

### 6. 查询所有记录

```
GET /query_all_records
```

**响应示例：**
```json
[
  { "id": 1, "homework_id": "hw001", ... },
  { "id": 2, "homework_id": "hw002", ... }
]
```

---

### 7. 删除作业视频

```
DELETE /delete_homework
```

**请求参数：**

| 参数 | 类型 | 位置 | 必填 | 说明 |
|-----|------|-----|-----|------|
| homework_id | string | Query | 是 | 作业ID |

**响应示例：**
```json
{
  "status": "success",
  "message": "作业 hw001 的所有视频已成功删除"
}
```

---

## AIChat API (端口 5000)

### 1. 创建会话

```
POST /api/sessions
```

**请求体：**
```json
{
  "user_id": "student001",
  "model": "Qwen",
  "role": "student"
}
```

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| user_id | string | 是 | 用户ID（学生ID或教师ID） |
| model | string | 否 | 模型名称，默认使用本地模型 |
| role | string | 否 | 用户角色：student（默认）或 teacher |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "session_id": 1,
    "session": {
      "session_id": 1,
      "messages": [
        {
          "role": "system",
          "content": "You are a Personal Coach AI..."
        },
        {
          "role": "assistant",
          "content": "你好！我是你的专属AI运动私教..."
        }
      ],
      "model": "local",
      "title": "New Chat-2024-01-15 10:30",
      "role": "student"
    },
    "welcome_message": {
      "role": "assistant",
      "content": "你好！我是你的专属AI运动私教。我已经同步了你近期的运动考核数据..."
    }
  }
}
```

**前端处理：**
1. 保存 `session_id` 用于后续消息发送
2. 显示 `welcome_message.content` 作为 AI 欢迎语
3. 教师角色的欢迎语不同

---

### 2. 获取用户所有会话

```
GET /api/sessions?user_id={user_id}
```

**请求参数：**

| 参数 | 类型 | 位置 | 必填 | 说明 |
|-----|------|-----|-----|------|
| user_id | string | Query | 是 | 用户ID |

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "session_id": 1,
      "title": "俯卧撑训练",
      "model": "local",
      "role": "student"
    },
    {
      "session_id": 2,
      "title": "深蹲技巧",
      "model": "local",
      "role": "student"
    }
  ]
}
```

---

### 3. 获取会话详情

```
GET /api/sessions/{session_id}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "session_id": 1,
    "messages": [
      { "role": "system", "content": "..." },
      { "role": "assistant", "content": "你好！我是..." },
      { "role": "user", "content": "我的俯卧撑怎么做不好？" },
      { "role": "assistant", "content": "根据你的数据，我建议..." }
    ],
    "model": "local",
    "title": "俯卧撑训练",
    "role": "student"
  }
}
```

---

### 4. 发送消息（核心接口）

```
POST /api/sessions/{session_id}/messages
```

**请求体：**
```json
{
  "message": "我的俯卧撑正确率不高，怎么改进？",
  "model": "Qwen"
}
```

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| message | string | 是 | 用户消息内容 |
| model | string | 否 | 指定模型，不填使用会话默认模型 |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "session": {
      "session_id": 1,
      "messages": [...]
    },
    "response": "同学你好！我注意到你的俯卧撑正确率还有提升空间。根据你最近的训练数据..."
  }
}
```

**前端处理：**
1. 显示 `response` 作为 AI 回复
2. 更新本地会话消息列表

---

### 5. 删除会话

```
DELETE /api/sessions/{session_id}
```

**响应示例：**
```json
{
  "success": true,
  "message": "会话已删除"
}
```

---

### 6. 清空会话消息

```
POST /api/sessions/{session_id}/clear
```

**响应示例：**
```json
{
  "success": true,
  "message": "会话已清空"
}
```

---

### 7. 导出会话

```
GET /api/sessions/{session_id}/export
```

**响应：** 返回 Markdown 文件下载

---

### 8. 获取模型信息

```
GET /api/models
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "model": "local",
    "model_path": "./models/Qwen2.5-7B-PE-Sports",
    "is_finetuned": true,
    "base_model": "./models/Qwen/Qwen2___5-7B-Instruct",
    "quantization": "4-bit"
  }
}
```

---

### 9. 生成 AI 分析报告（核心接口）

```
POST /api/analysis/generate
```

#### 9.1 作业反馈分析

**请求体：**
```json
{
  "student_id": "student001",
  "homework_id": "hw001",
  "analysis_type": "homework_feedback",
  "query": "分析我的深蹲表现"
}
```

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| student_id | string | 是 | 学生ID |
| homework_id | string | 是 | 作业ID（作业反馈必填） |
| analysis_type | string | 是 | 分析类型：homework_feedback |
| query | string | 否 | 用户查询内容 |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "report": "## 总体评价\n你的深蹲动作整体表现良好...\n\n## 错误分析\n主要问题在于...\n\n## 改进建议\n建议你...",
    "analysis_type": "homework_feedback"
  }
}
```

#### 9.2 个性化训练建议

**请求体：**
```json
{
  "student_id": "student001",
  "analysis_type": "personalized_tips",
  "student_info": {
    "height": 175,
    "weight": 65
  },
  "query": "根据我的情况给出长期训练建议"
}
```

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| student_id | string | 是 | 学生ID |
| homework_id | string | 否 | 作业ID（个性化建议不需要） |
| analysis_type | string | 是 | 分析类型：personalized_tips |
| student_info | object | 否 | 学生个人信息（身高、体重等） |
| query | string | 否 | 用户查询内容 |

---

### 10. 查询分析报告

```
GET /api/analysis/query?student_id={student_id}&homework_id={homework_id}&analysis_type={analysis_type}
```

**请求参数：**

| 参数 | 类型 | 位置 | 必填 | 说明 |
|-----|------|-----|-----|------|
| student_id | string | Query | 是 | 学生ID |
| homework_id | string | Query | 否 | 作业ID |
| analysis_type | string | Query | 否 | 分析类型 |

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "homework_id": "hw001",
      "student_id": "student001",
      "pose_type": "squat",
      "analysis_type": "homework_feedback",
      "report_content": "## 总体评价\n...",
      "created_at": "2024-01-15 10:30:00"
    }
  ]
}
```

---

### 11. 获取最近分析记录

```
GET /api/analysis/recent?student_id={student_id}&limit={limit}
```

**请求参数：**

| 参数 | 类型 | 位置 | 必填 | 说明 |
|-----|------|-----|-----|------|
| student_id | string | Query | 否 | 学生ID，不填返回所有 |
| limit | int | Query | 否 | 返回数量，默认 10 |

---

## 错误处理

### AIChat 错误响应格式

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

**常见错误：**

| 错误信息 | 说明 | 处理建议 |
|---------|------|---------|
| 用户ID不能为空 | 未提供 user_id | 检查请求参数 |
| 会话不存在 | session_id 无效 | 重新创建会话 |
| 消息内容不能为空 | 未提供消息 | 检查请求体 |
| 不支持的分析类型 | analysis_type 错误 | 使用 homework_feedback 或 personalized_tips |

### Yolo_backend 错误响应格式

Yolo_backend 使用 HTTP 状态码表示错误：

| 状态码 | 说明 |
|-------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**错误响应示例：**
```json
{
  "detail": "未找到相关记录"
}
```

---

## 调用示例

### 示例 1：学生上传作业视频

```javascript
async function uploadHomeworkVideo(homeworkId, studentId, poseType, videoFile) {
  const formData = new FormData();
  formData.append('file', videoFile);

  const response = await fetch(
    `http://localhost:8000/process_and_save_video?homework_id=${homeworkId}&student_id=${studentId}&pose_type=${poseType}`,
    { method: 'POST', body: formData }
  );

  // 处理 SSE 流
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let finalResult = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6));

        switch (event.event) {
          case 'init':
            console.log('初始化:', event.data.message);
            break;
          case 'frame':
            // 更新实时预览
            document.getElementById('preview').src = `data:image/jpeg;base64,${event.data.image}`;
            document.getElementById('count').textContent = event.data.max_count;
            break;
          case 'final_stats':
            finalResult = event.data;
            console.log('处理完成:', finalResult);
            break;
          case 'error':
            console.error('错误:', event.data.message);
            break;
        }
      }
    }
  }

  return finalResult;
}
```

### 示例 2：AI 聊天对话

```javascript
// 1. 创建会话
async function createChatSession(userId, role = 'student') {
  const response = await fetch('http://localhost:5000/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, role })
  });
  const data = await response.json();

  if (data.success) {
    return {
      sessionId: data.data.session_id,
      welcomeMessage: data.data.welcome_message.content
    };
  }
  throw new Error(data.error);
}

// 2. 发送消息
async function sendMessage(sessionId, message) {
  const response = await fetch(`http://localhost:5000/api/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  const data = await response.json();

  if (data.success) {
    return data.data.response;
  }
  throw new Error(data.error);
}

// 使用示例
const session = await createChatSession('student001');
console.log('AI:', session.welcomeMessage);

const reply = await sendMessage(session.sessionId, '我的俯卧撑怎么做不好？');
console.log('AI:', reply);
```

### 示例 3：生成分析报告

```javascript
async function generateReport(studentId, homeworkId) {
  const response = await fetch('http://localhost:5000/api/analysis/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      homework_id: homeworkId,
      analysis_type: 'homework_feedback'
    })
  });
  const data = await response.json();

  if (data.success) {
    return data.data.report;
  }
  throw new Error(data.error);
}

// 使用
const report = await generateReport('student001', 'hw001');
document.getElementById('report').innerHTML = marked.parse(report); // 使用 marked.js 渲染 Markdown
```

---

## 附录

### A. 完整接口列表

#### Yolo_backend (8000)

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /health | 健康检查 |
| GET | /supported_poses | 支持的动作类型 |
| POST | /process_and_save_video | 处理并保存视频 |
| GET | /get_processed_video | 获取处理后的视频 |
| GET | /query_records | 查询运动记录 |
| GET | /query_all_records | 查询所有记录 |
| DELETE | /delete_homework | 删除作业视频 |

#### AIChat (5000)

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /api/sessions | 创建会话 |
| GET | /api/sessions | 获取用户所有会话 |
| GET | /api/sessions/{id} | 获取会话详情 |
| DELETE | /api/sessions/{id} | 删除会话 |
| POST | /api/sessions/{id}/messages | 发送消息 |
| POST | /api/sessions/{id}/clear | 清空会话 |
| GET | /api/sessions/{id}/export | 导出会话 |
| GET | /api/models | 获取模型信息 |
| POST | /api/analysis/generate | 生成分析报告 |
| GET | /api/analysis/query | 查询分析报告 |
| GET | /api/analysis/recent | 获取最近分析 |

### B. 环境变量配置

**Yolo_backend：**
```bash
# 无需配置，默认使用本地模型
```

**AIChat：**
```bash
YOLO_BASE_URL=http://localhost:8000  # Yolo_backend 地址
MODEL_PATH=./models/Qwen2.5-7B-PE-Sports  # 模型路径
MAX_TOKENS=2048  # 最大生成长度
TEMPERATURE=0.7  # 生成温度
LOAD_IN_4BIT=true  # 4-bit 量化
```

---

**文档版本：** 1.0.0
**更新日期：** 2024-01-15
**维护者：** 后端开发组
