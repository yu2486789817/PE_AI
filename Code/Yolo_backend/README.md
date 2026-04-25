# Yolo_backend - AI 健身动作识别服务

## 模块概述

Yolo_backend 是一个基于计算机视觉的健身动作识别服务，使用 YOLOv8-pose 模型进行人体姿态估计，能够实时识别和计数多种健身动作，并提供动作质量评估和错误检测。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Yolo_backend 架构                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   FastAPI   │───▶│   AIGym     │───▶│   YOLOv8-pose      │ │
│  │   API 层    │    │   核心类    │    │   模型推理         │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                  │                                    │
│         │                  ▼                                    │
│         │          ┌─────────────────────────────────────┐     │
│         │          │         运动跟踪器                   │     │
│         │          │  ┌───────────┬───────────┬────────┐ │     │
│         │          │  │ Pushup    │ Squat     │Deadlift│ │     │
│         │          │  │ Tracker   │ Tracker   │Tracker │ │     │
│         │          │  └───────────┴───────────┴────────┘ │     │
│         │          └─────────────────────────────────────┘     │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────┐    ┌─────────────┐                          │
│  │   SQLite    │    │   文件存储   │                          │
│  │   数据库    │    │   (视频)     │                          │
│  └─────────────┘    └─────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 核心组件说明

### 1. AIGym 核心类 (`ai_gym.py`)

AIGym 是整个识别系统的核心类，继承自 Ultralytics 的 BaseSolution。

**主要职责：**
- 加载和管理 YOLOv8-pose 模型
- 协调运动跟踪器进行动作识别
- 管理视频帧处理流程
- 收集和返回处理结果

**关键属性：**
```python
class AIGym(BaseSolution):
    def __init__(self, kpts_to_check, line_thickness=2, pose_type="pushup", **kwargs):
        self.pose_type = pose_type           # 运动类型
        self.kpts = kpts_to_check            # 关键点索引
        self.poseup_angle = ...              # 上升角度阈值
        self.posedown_angle = ...            # 下降角度阈值
        self.tracker = ...                   # 运动跟踪器实例
        self.result_data = {}                # 结果数据
```

**处理流程：**
1. 接收视频帧
2. 调用 YOLO 模型进行姿态估计
3. 提取人体关键点
4. 计算关节角度
5. 调用对应跟踪器进行状态判断
6. 返回处理后的帧和计数结果

### 2. 运动跟踪器架构

每种运动类型都有独立的 Tracker 类，遵循统一的设计模式：

```
BaseTracker (隐式接口)
├── PushupTracker   (俯卧撑)
├── SquatTracker    (深蹲)
└── DeadliftTracker (硬拉)
```

**Tracker 类通用结构：**
```python
class XxxTracker:
    def __init__(self):
        self.state_tracker = {...}      # 状态跟踪字典
        self.thresholds = {...}         # 阈值配置
        self.FEEDBACK_ID_MAP = {...}    # 错误反馈映射
        self.events = []                # 事件记录

    def track(self, k, im0, ind, count, fps=30):
        """主处理逻辑"""
        pass

    def _get_state(self, angle):
        """根据角度判断状态"""
        pass

    def _update_state_sequence(self, state):
        """更新状态序列"""
        pass

    def _record_events(self, frame_index, fps):
        """记录事件"""
        pass
```

### 3. 关键点检测算法原理

**YOLOv8-pose 关键点索引：**
```
0: 鼻子    1: 左眼    2: 右眼    3: 左耳    4: 右耳
5: 左肩    6: 右肩    7: 左肘    8: 右肘    9: 左腕
10: 右腕   11: 左髋   12: 右髋   13: 左膝   14: 右膝
15: 左踝   16: 右踝
```

**各运动使用的关键点：**
| 运动类型 | 关键点组合 | 用途 |
|---------|-----------|------|
| Pushup  | 6, 8, 10  | 右肩-右肘-右腕 |
| Squat   | 12, 14, 16| 右髋-右膝-右踝 |
| Deadlift| 6, 12, 14 | 右肩-右髋-右膝 |

### 4. 角度计算与状态判断逻辑

**角度计算函数 (`function.py`)：**
```python
def calculate_angle(point1, point2, point3=None, reference_direction='horizontal'):
    """
    计算角度：
    - 三点夹角：point1-point2-point3
    - 两点与参考方向夹角：point1-point2 与 horizontal/vertical
    """
```

**状态判断逻辑（以俯卧撑为例）：**
```
状态序列：s1 → s2 → s3 → s1 (完成一次)

s1 (NORMAL): 肘部角度 155°-180° (上升完成)
s2 (TRANS):  肘部角度 110°-150° (下降中)
s3 (PASS):   肘部角度 55°-100°  (下放到底)

完整动作：s1 → s2 → s3 → s1
```

### 5. 错误检测机制

**俯卧撑错误类型：**
| 错误代码 | 描述 | 检测条件 |
|---------|------|---------|
| BACK ARCHED | 背部拱起 | 背部角度 > 90° |
| INSUFFICIENT RANGE | 动作幅度不够 | 未达到 s3 状态 |
| BODY SINKING | 身体下沉 | 髋肩距离比 < 0.85 |

**深蹲错误类型：**
| 错误代码 | 描述 | 检测条件 |
|---------|------|---------|
| LEAN BACKWARDS | 后倾过多 | 髋角度 > 50° |
| LEAN FORWARD | 前倾过多 | 髋角度 < 10° |
| KNEE OVER TOE | 膝盖超脚尖 | 踝角度 > 45° |
| SQUAT TOO DEEP | 下蹲过深 | 膝角度 > 95° |

**硬拉错误类型：**
| 错误代码 | 描述 | 检测条件 |
|---------|------|---------|
| BACK TOO ARCHED | 背部过度弯曲 | 肩髋角度 > 50° |
| KNEE TOO LOW | 膝盖过低 | 膝踝角度 > 45° |
| ARM BENDING | 手臂弯曲 | 手臂角度 < 150° |

## 识别算法优化建议

### 当前算法分析

**优点：**
1. 基于状态机的动作判断逻辑清晰
2. 支持多种运动类型
3. 实时反馈机制完善

**可改进点：**
1. 阈值固定，无法适应不同体型
2. 单帧判断，缺乏时序平滑
3. 仅使用单侧关键点
4. 对遮挡和光照敏感

### 改进方向

#### 1. 多关键点融合
```python
# 当前：仅使用右侧关键点
right_shoulder = k[6]
right_elbow = k[8]

# 改进：融合左右两侧，取置信度高的
def get_reliable_keypoint(k, left_idx, right_idx, confidence_threshold=0.5):
    left_conf = k[left_idx][2] if len(k[left_idx]) > 2 else 1.0
    right_conf = k[right_idx][2] if len(k[right_idx]) > 2 else 1.0

    if left_conf > confidence_threshold and right_conf > confidence_threshold:
        return (k[left_idx] + k[right_idx]) / 2  # 平均
    elif left_conf > right_conf:
        return k[left_idx]
    else:
        return k[right_idx]
```

#### 2. 时序平滑
```python
from collections import deque

class SmoothedTracker:
    def __init__(self, window_size=5):
        self.angle_history = deque(maxlen=window_size)

    def get_smoothed_angle(self, current_angle):
        self.angle_history.append(current_angle)
        # 加权移动平均
        weights = [0.1, 0.15, 0.2, 0.25, 0.3][-len(self.angle_history):]
        return sum(a * w for a, w in zip(self.angle_history, weights)) / sum(weights)
```

#### 3. 自适应阈值
```python
class AdaptiveThreshold:
    def __init__(self):
        self.baseline_angles = []

    def calibrate(self, calibration_frames):
        """校准阶段：收集用户的基础姿态"""
        self.baseline_angles = calibration_frames
        self.user_specific_threshold = self._calculate_personal_threshold()

    def _calculate_personal_threshold(self):
        """根据用户体型计算个性化阈值"""
        # 基于用户肢体长度比例调整阈值
        pass
```

#### 4. 置信度过滤
```python
def filter_low_confidence_keypoints(keypoints, threshold=0.5):
    """过滤低置信度的关键点"""
    filtered = keypoints.copy()
    for i, kp in enumerate(keypoints):
        if len(kp) > 2 and kp[2] < threshold:
            # 使用上一帧或插值
            filtered[i] = interpolate_keypoint(keypoints, i)
    return filtered
```

## 数据库设计

### exercise_feedback 表

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INTEGER | 主键，自增 |
| homework_id | VARCHAR(50) | 作业ID |
| student_id | VARCHAR(50) | 学生ID |
| pose_type | VARCHAR(20) | 动作类型 |
| uploaded_at | TIMESTAMP | 上传时间 |
| original_video_path | VARCHAR(255) | 原始视频路径 |
| processed_video_path | VARCHAR(255) | 处理后视频路径 |
| total_count | INTEGER | 总动作次数 |
| correct_count | INTEGER | 正确次数 |
| incorrect_count | INTEGER | 错误次数 |
| feedback_json | TEXT | AI反馈数据(JSON) |
| video_duration | FLOAT | 视频时长(秒) |

### feedback_json 结构

```json
{
  "events": [
    {
      "event_id": "pushup_1",
      "type": "PUSHUP_COMPLETE_CORRECT",
      "frame": 120,
      "timestamp": 4.0,
      "correct_count": 1,
      "incorrect_count": 0
    }
  ],
  "performance": {
    "total_count": 12,
    "correct_count": 10,
    "incorrect_count": 2,
    "accuracy_rate": 83.33
  },
  "video_info": {
    "total_frames": 360,
    "processed_frames": 180,
    "fps": 30,
    "duration": 12.0
  }
}
```

## API 接口文档

详见现有 README.md 中的 API 文档部分，此处列出核心接口：

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/health` | GET | 健康检查 |
| `/supported_poses` | GET | 获取支持的动作类型 |
| `/stream_process_video` | POST | 流式视频处理 |
| `/process_and_save_video` | POST | 处理并保存视频 |
| `/get_processed_video` | GET | 获取处理后的视频 |
| `/query_records` | GET | 查询记录 |
| `/api/student/all-records/{student_id}` | GET | 获取学生所有记录 |

## 扩展指南：添加新运动类型

### 步骤 1：创建 Tracker 类

在 `Code/Yolo_backend/` 目录下创建新文件，如 `pullup.py`：

```python
import cv2
import numpy as np
from function import draw_text, calculate_angle, _show_feedback
import time

class PullupTracker:
    def __init__(self):
        self.state_tracker = {
            'state_seq': [],
            'DISPLAY_TEXT': np.full((3,), False),
            'COUNT_FRAMES': np.zeros((3,), dtype=np.int64),
            'INCORRECT_POSTURE': False,
            'curr_state': None,
            'PULLUP_COUNT': 0,
            'IMPROPER_PULLUP': 0
        }

        self.FEEDBACK_ID_MAP = {
            0: ('INCOMPLETE RANGE', 215, (255, 80, 80)),
            1: ('SWINGING', 170, (255, 80, 80)),
            2: ('KNEE BENDING', 125, (255, 80, 80))
        }

        self.thresholds = self.get_thresholds_beginner()

    def get_thresholds_beginner(self):
        return {
            'SHOULDER_ELBOW_ANGLE': {
                'NORMAL': (160, 180),  # 上升完成
                'TRANS': (100, 140),   # 过渡
                'PASS': (30, 80)       # 下放
            },
            # ... 其他阈值
        }

    def track(self, k, im0, ind, count, fps=30):
        # 实现识别逻辑
        pass
```

### 步骤 2：在 ai_gym.py 中注册

```python
# 在 ai_gym.py 顶部添加导入
from pullup import PullupTracker

# 在 AIGym.__init__ 中添加条件分支
if pose_type == "pullup":
    self.tracker = PullupTracker()
```

### 步骤 3：在 main.py 中添加支持

```python
@app.get("/supported_poses")
async def get_supported_poses():
    return {
        "supported_poses": [
            "pushup", "squat", "deadlift", "pullup"  # 添加新类型
        ]
    }
```

### 步骤 4：更新关键点配置

在 `main.py` 的 `create_gym_object` 方法中添加：

```python
elif pose_type in ["pullup"]:
    kpts_to_check = [6, 8, 10]  # 或其他合适的关键点
```

## 部署说明

### 环境要求

- Python 3.9+
- CUDA 11.0+ (GPU 加速)
- 内存：至少 8GB
- GPU 显存：至少 4GB

### 安装依赖

```bash
cd Code/Yolo_backend
pip install ultralytics fastapi uvicorn opencv-python numpy
```

### 启动服务

```bash
# 开发模式
python main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir ultralytics fastapi uvicorn opencv-python-headless numpy

# 下载模型
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n-pose.pt')"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 性能优化建议

1. **模型量化**：使用 INT8 量化减少显存占用
2. **批处理**：对多帧进行批量推理
3. **跳帧处理**：当前已实现 SKIP_FACTOR=2
4. **异步处理**：使用 asyncio 并行处理多个请求
5. **缓存机制**：对相同视频的重复请求进行缓存

## 常见问题

### Q: 识别准确率不高怎么办？
A: 确保视频光线充足，人物在画面中清晰可见，背景不要太复杂。

### Q: 如何调整阈值？
A: 修改各 Tracker 类中的 `get_thresholds_beginner()` 方法中的阈值配置。

### Q: 支持多人识别吗？
A: 当前版本仅支持单人识别，多人场景需要修改 `ai_gym.py` 中的处理逻辑。

---

## 上游服务接口文档

本章节面向上游服务（PE-AI-Backend、前端）开发者，说明如何调用 Yolo_backend 提供的接口。

### 服务信息

| 配置项 | 值 |
|-------|-----|
| 服务名称 | Yolo_backend |
| 默认端口 | 8000 |
| 基础 URL | `http://localhost:8000` |
| 协议 | HTTP + SSE |

### 接口概览

| 接口 | 方法 | 调用方 | 业务场景 |
|-----|------|-------|---------|
| `/health` | GET | PE-AI-Backend | 健康检查 |
| `/supported_poses` | GET | 前端 | 获取支持的动作类型 |
| `/process_and_save_video` | POST | 前端 | 学生提交作业视频 |
| `/get_processed_video` | GET | 前端 | 获取处理后的视频 |
| `/query_records` | GET | 前端/PE-AI-Backend | 查询 AI 评价结果 |
| `/api/student/all-records/{student_id}` | GET | AIChat | 获取学生历史数据 |

---

### 1. 健康检查

**接口：** `GET /health`

**调用方：** PE-AI-Backend（服务启动检查、负载均衡健康探测）

**业务场景：** 确认 Yolo_backend 服务正常运行

**请求示例：**
```bash
curl http://localhost:8000/health
```

**响应格式：**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "active_sessions": 0
}
```

**响应字段说明：**
| 字段 | 类型 | 说明 |
|-----|------|------|
| status | string | 服务状态，"healthy" 表示正常 |
| model_loaded | boolean | YOLO 模型是否加载成功 |
| active_sessions | integer | 当前正在处理的视频会话数 |

---

### 2. 获取支持的动作类型

**接口：** `GET /supported_poses`

**调用方：** 前端（作业提交页面初始化时）

**业务场景：** 前端需要展示可选的动作类型列表

**请求示例：**
```bash
curl http://localhost:8000/supported_poses
```

**响应格式：**
```json
{
  "supported_poses": ["pushup", "squat", "deadlift"]
}
```

---

### 3. 处理并保存视频（核心接口）

**接口：** `POST /process_and_save_video`

**调用方：** 前端（学生提交作业）

**业务场景：** 学生上传作业视频，AI 进行动作识别和计数

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|-------|------|------|------|------|
| homework_id | Query | string | 是 | 作业ID，用于关联作业和存储路径 |
| student_id | Query | string | 是 | 学生ID，用于关联学生和存储路径 |
| pose_type | Query | string | 否 | 动作类型，默认 "pushup"，可选: pushup/squat/deadlift |
| file | Body | binary | 是 | 视频文件 (multipart/form-data) |

**请求示例：**
```bash
curl -X POST \
  -F "file=@student_video.mp4" \
  "http://localhost:8000/process_and_save_video?homework_id=hw001&student_id=stu001&pose_type=pushup"
```

**响应格式：** SSE 流式响应

**SSE 事件类型：**

#### 3.1 初始化事件 (init)
```javascript
data: {
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
```javascript
data: {
  "event": "frame",
  "data": {
    "frame_index": 10,
    "processed_frame_count": 5,
    "count": 2,
    "max_count": 2,
    "image": "base64_encoded_jpeg_image"
  }
}
```

#### 3.3 最终统计事件 (final_stats)
```javascript
data: {
  "event": "final_stats",
  "data": {
    "message": "视频处理完成",
    "max_count": 12,              // 总动作次数
    "processed_frame_count": 180, // 处理的帧数
    "total_time": 12.0,           // 视频时长（秒）
    "saved_path": "homework/hw001/stu001/processed_video.mp4",
    "video_url": "/get_processed_video?homework_id=hw001&student_id=stu001"
  }
}
```

#### 3.4 错误事件 (error)
```javascript
data: {
  "event": "error",
  "data": {
    "message": "错误描述信息"
  }
}
```

**前端处理流程：**
```javascript
async function submitVideo(file, homeworkId, studentId, poseType) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `http://localhost:8000/process_and_save_video?homework_id=${homeworkId}&student_id=${studentId}&pose_type=${poseType}`,
    { method: 'POST', body: formData }
  );

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let result = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const { event, data } = JSON.parse(line.slice(6));

        switch (event) {
          case 'init':
            console.log('初始化:', data.message);
            break;
          case 'frame':
            // 更新预览画面
            updatePreview(data.image);
            break;
          case 'final_stats':
            result = data;
            // 保存 AI 评价结果到后端
            await saveAIFeedback(homeworkId, studentId, data);
            break;
          case 'error':
            throw new Error(data.message);
        }
      }
    }
  }

  return result;
}
```

---

### 4. 获取处理后的视频

**接口：** `GET /get_processed_video`

**调用方：** 前端（查看作业提交详情）

**业务场景：** 播放或下载处理后的视频

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|-------|------|------|------|------|
| homework_id | Query | string | 是 | 作业ID |
| student_id | Query | string | 是 | 学生ID |
| download | Query | boolean | 否 | 是否作为附件下载，默认 false |

**请求示例：**
```bash
# 流式预览
curl "http://localhost:8000/get_processed_video?homework_id=hw001&student_id=stu001"

# 下载文件
curl "http://localhost:8000/get_processed_video?homework_id=hw001&student_id=stu001&download=true" -o processed.mp4
```

**响应格式：**
- `download=false`：SSE 流式返回视频帧
- `download=true`：返回 MP4 文件

---

### 5. 查询记录

**接口：** `GET /query_records`

**调用方：** 前端（查看 AI 评价详情）、PE-AI-Backend（获取 AI 反馈）

**业务场景：** 查看学生作业的 AI 评价结果

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|-------|------|------|------|------|
| homework_id | Query | string | 是 | 作业ID |
| student_id | Query | string | 是 | 学生ID |
| pose_type | Query | string | 否 | 动作类型，不传则返回所有类型 |

**请求示例：**
```bash
curl "http://localhost:8000/query_records?homework_id=hw001&student_id=stu001&pose_type=pushup"
```

**响应格式：**
```json
[
  {
    "id": 1,
    "homework_id": "hw001",
    "student_id": "stu001",
    "pose_type": "pushup",
    "total_count": 12,
    "correct_count": 10,
    "incorrect_count": 2,
    "feedback_json": "{\"events\":[...],\"performance\":{...}}",
    "video_duration": 12.0,
    "uploaded_at": "2023-01-01 12:00:00",
    "processed_video_path": "homework/hw001/stu001/processed_video.mp4"
  }
]
```

**上游服务处理：**
```java
// PE-AI-Backend 调用示例
public AIFeedback getAIFeedback(String homeworkId, String studentId, String poseType) {
    String url = String.format("%s/query_records?homework_id=%s&student_id=%s&pose_type=%s",
        yoloBaseUrl, homeworkId, studentId, poseType);
    
    ResponseEntity<List> response = restTemplate.getForEntity(url, List.class);
    List<Map<String, Object>> records = response.getBody();
    
    if (records != null && !records.isEmpty()) {
        Map<String, Object> record = records.get(0);
        return new AIFeedback(
            (Integer) record.get("correct_count"),
            (Integer) record.get("incorrect_count"),
            (String) record.get("feedback_json")
        );
    }
    return null;
}
```

---

### 6. 获取学生所有记录

**接口：** `GET /api/student/all-records/{student_id}`

**调用方：** AIChat 服务（生成个性化报告时）

**业务场景：** AI 需要获取学生的历史运动数据来生成个性化训练建议

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|-------|------|------|------|------|
| student_id | Path | string | 是 | 学生ID |

**请求示例：**
```bash
curl "http://localhost:8000/api/student/all-records/stu001"
```

**响应格式：**
```json
[
  {
    "id": 12,
    "homework_id": "hw001",
    "student_id": "stu001",
    "pose_type": "pushup",
    "total_count": 15,
    "correct_count": 12,
    "incorrect_count": 3,
    "feedback_json": "{\"events\":[...],\"performance\":{...}}",
    "video_duration": 6.0,
    "uploaded_at": "2023-12-01 10:30:00"
  },
  {
    "id": 8,
    "homework_id": "hw002",
    "student_id": "stu001",
    "pose_type": "squat",
    "total_count": 20,
    "correct_count": 18,
    "incorrect_count": 2,
    "feedback_json": "{\"events\":[...],\"performance\":{...}}",
    "video_duration": 8.0,
    "uploaded_at": "2023-11-28 14:15:00"
  }
]
```

**AIChat 服务调用示例：**
```python
# report_module.py 中的调用
def get_yolo_student_all_records(student_id):
    """获取学生所有运动记录，用于生成个性化建议"""
    url = f"{YOLO_BASE_URL}/api/student/all-records/{student_id}"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        return response.json()
    return None
```

---

## 数据库关联设计

### 与 MySQL 数据库的关系

```
MySQL (se_project)                    SQLite (exercise_feedback)
┌─────────────────────┐               ┌─────────────────────────┐
│ homework            │               │ exercise_feedback       │
│ ─────────────────── │               │ ─────────────────────── │
│ id (PK)            │◄──────────────│ homework_id             │
│ course_id          │               │ student_id              │
│ title              │               │ pose_type               │
│ deadline           │               │ total_count             │
└─────────────────────┘               │ correct_count           │
                                      │ incorrect_count         │
┌─────────────────────┐               │ feedback_json           │
│ submit              │               │ video_duration          │
│ ─────────────────── │               │ processed_video_path    │
│ id (PK)            │               └─────────────────────────┘
│ homework_id (FK)   │◄──────────────┘
│ student_id         │
│ video_url          │
│ score              │
│ AI_feedback        │◄── 可从 feedback_json 提取
│ teacher_feedback   │
└─────────────────────┘
```

### 数据同步流程

1. **学生提交视频**：前端调用 `/process_and_save_video`
2. **AI 处理完成**：结果存入 SQLite `exercise_feedback` 表
3. **前端获取结果**：调用 `/query_records` 获取 AI 评价
4. **保存到 MySQL**：前端将 AI 评价保存到 `submit.AI_feedback` 字段

---

## 错误码定义

| HTTP 状态码 | 说明 | 处理建议 |
|------------|------|---------|
| 200 | 成功 | 正常处理 |
| 400 | 请求参数错误 | 检查参数格式和必填项 |
| 404 | 资源不存在 | 检查 homework_id 和 student_id |
| 422 | 参数验证失败 | 检查 pose_type 是否在支持列表中 |
| 500 | 服务器内部错误 | 查看服务日志，可能是模型加载失败 |

---

## 服务配置

### PE-AI-Backend 配置

在 `application.yml` 中配置 Yolo_backend 地址：

```yaml
ai:
  yolo:
    base-url: http://localhost:8000
```

### 前端代理配置

在 `vite.config.js` 中配置代理：

```javascript
export default defineConfig({
  server: {
    proxy: {
      '/video': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```
