import asyncio
import base64
import json
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
from ultralytics import YOLO
from ai_gym import AIGym
import tempfile
import os
import uvicorn
import traceback
import logging
import time
import shutil
from database import (
    init_database,
    insert_exercise_feedback,
    get_exercise_feedback,
    get_exercise_feedback_by_id,
    get_student_all_records,
    get_records_by_homework_student,
    get_all_records
)
from typing import List, Optional
from datetime import datetime

# ================= 路径配置 =================
# 获取当前脚本所在目录，确保无论在哪里运行都使用正确的路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
HOMEWORK_DIR = os.path.join(SCRIPT_DIR, "homework")

app = FastAPI(title="AI Gym API", description="健身动作识别后端API")

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储临时目录，以便稍后清理（必须在 shutdown_event 之前定义）
temp_dirs = {}  # 存储临时目录信息，包括创建时间和路径

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Final-Count", "X-Total-Frames", "X-Total-Time"],  # 添加这行
)


# 添加一个中间件确保所有响应都有CORS头部
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


class SSEStreamingResponse(StreamingResponse):
    """自定义StreamingResponse以支持SSE"""

    def __init__(self, content, status_code=200, headers=None, media_type="text/event-stream"):
        super().__init__(content, status_code, headers, media_type)


class VideoProcessor:
    def __init__(self):
        self.model = None
        self.gym_objects = {}

    def load_model(self):
        """加载YOLO模型"""
        if self.model is None:
            # 模型路径列表，按优先级尝试
            model_paths = [
                os.path.join(SCRIPT_DIR, "yolov8n-pose.pt"),  # 脚本目录
                os.path.join(MODELS_DIR, "yolov8n-pose.pt"),  # models 子目录
            ]

            for model_path in model_paths:
                try:
                    self.model = YOLO(model_path)
                    print(f"YOLO模型加载成功: {model_path}")
                    return
                except Exception as e:
                    print(f"尝试加载 {model_path} 失败: {e}")

            # 如果本地都没有，尝试自动下载到脚本目录
            try:
                print("尝试自动下载 YOLO 模型...")
                self.model = YOLO("yolov8n-pose.pt")
                # 下载成功后，模型会保存在当前目录，下次可以直接加载
                print("YOLO模型自动下载成功")
            except Exception as e:
                print(f"模型自动下载失败: {e}")
                raise e

    def create_gym_object(self, session_id: str, pose_type: str, fps: int = 30):
        """创建AIGym对象"""
        # 根据姿势类型设定关键点
        if pose_type in ["pushup"]:
            kpts_to_check = [6, 8, 10]
        elif pose_type in ["squat"]:
            kpts_to_check = [12, 14, 16]
        elif pose_type in ["deadlift"]:
            kpts_to_check = [6, 12, 14]
        else:
            kpts_to_check = [6, 8, 10]  # 默认关键点

        gym_object = AIGym(
            kpts_to_check=kpts_to_check,
            line_thickness=2,
            pose_type=pose_type,
            fps=fps
        )

        self.gym_objects[session_id] = gym_object
        return gym_object


# 添加 OPTIONS 方法处理程序
@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


video_processor = VideoProcessor()


@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    video_processor.load_model()
    # 初始化数据库
    init_database()


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理临时目录"""
    for temp_info in temp_dirs.values():
        try:
            shutil.rmtree(temp_info['path'])
        except Exception as e:
            logger.error(f"关闭时清理临时目录时出错: {e}")


def sse_format(event_type, data):
    """格式化SSE事件数据"""
    json_data = json.dumps({"event": event_type, "data": data})
    return f"data: {json_data}\n\n"


async def stream_process_video_endpoint(file_content: bytes, pose_type: str, save_path: str = None,
                                        homework_id: str = None, student_id: str = None):
    """流式处理视频并逐帧返回结果，可选保存到指定位置"""
    session_id = None
    cap = None
    out = None
    start_time = time.time()  # 记录开始时间

    try:
        logger.info("开始流式处理视频上传...")

        # 发送初始化事件
        yield sse_format("init", {"message": "开始处理视频"})

        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        tmp_file_path = os.path.join(temp_dir, "input_video.mp4")
        output_path = os.path.join(temp_dir, "output_video.mp4")

        # 生成临时目录ID并存储
        temp_id = str(uuid.uuid4())
        temp_dirs[temp_id] = {
            'path': temp_dir,
            'created_at': time.time(),
            'last_access': time.time()
        }

        # 将文件内容写入临时文件
        with open(tmp_file_path, "wb") as buffer:
            buffer.write(file_content)

        logger.info(f"视频已保存到 {tmp_file_path}")
        yield sse_format("init", {"message": "视频上传完成", "path": tmp_file_path})

        # 读取视频
        logger.info("尝试打开视频文件...")
        cap = cv2.VideoCapture(tmp_file_path)

        if not cap.isOpened():
            logger.error("无法打开视频文件")
            yield sse_format("error", {"message": "无法打开视频文件"})
            return

        # 获取视频信息
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps == 0:
            fps = 30

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        logger.info(f"视频信息: FPS={fps}, 宽度={width}, 高度={height}, 总帧数={frame_count}")
        yield sse_format("init", {
            "message": "视频信息获取完成",
            "fps": fps,
            "width": width,
            "height": height,
            "frame_count": frame_count
        })

        # 视频编码器设置
        SKIP_FACTOR = 1
        output_fps = fps / SKIP_FACTOR

        # 使用 MJPG 编码保存为 AVI（兼容性最好）
        # 后续可通过 FFmpeg 转换为 H.264 MP4（如果需要）
        temp_output_path = os.path.join(temp_dir, "temp_output.avi")
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(temp_output_path, fourcc, output_fps, (width, height), True)

        if not out.isOpened():
            yield sse_format("error", {"message": "无法创建输出视频文件"})
            return

        logger.info(f"临时视频文件创建成功: {temp_output_path}")

        # 创建gym对象
        session_id = f"session_{int(time.time() * 1000000) % 1000000}"
        logger.info(f"创建gym对象，session_id: {session_id}")
        gym_object = video_processor.create_gym_object(session_id, pose_type, fps)

        processed_frame_count = 0
        max_count = 0
        frame_index = 0

        # 处理每一帧
        logger.info("开始逐帧处理视频...")
        yield sse_format("init", {"message": "开始逐帧处理视频"})

        while True:
            frame_start_time = time.time()
            success, frame = cap.read()
            if not success:
                logger.info("视频读取完成")
                break

            # 跳帧处理
            if frame_index % SKIP_FACTOR != 0:
                frame_index += 1
                continue

            try:
                processed_frame, count = gym_object.monitor(frame)
                if processed_frame is not None:
                    # 写入处理后的帧到输出视频
                    out.write(processed_frame)

                    max_count = max(max_count, count)
                    processed_frame_count += 1

                    # 每隔一定帧数发送进度更新
                    if processed_frame_count % 5 == 0:  # 每5帧发送一次更新
                        # 将处理后的帧编码为JPEG并转换为base64
                        _, buffer = cv2.imencode('.jpg', processed_frame)
                        jpg_as_text = base64.b64encode(buffer).decode('utf-8')

                        yield sse_format("frame", {
                            "frame_index": frame_index,
                            "processed_frame_count": processed_frame_count,
                            "count": count,
                            "max_count": max_count,
                            "image": jpg_as_text
                        })

                        # 短暂休眠以避免过快发送数据
                        await asyncio.sleep(0.01)

                frame_index += 1

            except Exception as e:
                error_msg = f"处理第 {frame_index} 帧时出错: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                yield sse_format("error", {"message": error_msg})
                continue

            frame_end_time = time.time()
            frame_process_time = frame_end_time - frame_start_time
            if processed_frame_count % 10 == 0:
                logger.info(f"帧 {frame_index} 处理时间: {frame_process_time:.3f}秒")

        logger.info(f"视频处理完成，共处理 {processed_frame_count} 帧")

        # 确保视频文件正确关闭
        out.release()
        cap.release()

        # 使用 FFmpeg 将 AVI 转换为 H.264 MP4（浏览器兼容）
        # 如果没有 FFmpeg，则直接使用 AVI 文件
        import subprocess
        try:
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', temp_output_path,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                '-pix_fmt', 'yuv420p', output_path
            ]
            subprocess.run(ffmpeg_cmd, capture_output=True, check=True, timeout=60)
            logger.info(f"FFmpeg 转换成功: {output_path}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(f"FFmpeg 转换失败，使用原始 AVI: {e}")
            # 如果 FFmpeg 失败，直接复制 AVI 文件
            output_path = temp_output_path

        # 如果需要保存到指定位置
        if save_path:
            # 创建保存目录
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            # 复制处理后的视频到目标位置
            shutil.copy2(output_path, save_path)
            # 添加日志信息，记录保存视频后的状态
            logger.info(f"视频已保存到指定位置: {save_path}")
            logger.info(f"保存目录是否存在: {os.path.exists(os.path.dirname(save_path))}")
            logger.info(f"保存的文件是否存在: {os.path.exists(save_path)}")
            logger.info(f"保存的文件大小: {os.path.getsize(save_path) if os.path.exists(save_path) else 0} 字节")

        # 读取处理后的视频文件
        with open(output_path, "rb") as video_file:
            processed_video = video_file.read()

        # 发送最终统计信息
        final_stats = {
            "message": "视频处理完成",
            "max_count": max_count,
            "processed_frame_count": processed_frame_count,
            "total_time": frame_index / fps if fps > 0 else 0,
            "output_path": output_path,
            "video_size": len(processed_video)
        }

        if save_path:
            final_stats["saved_path"] = save_path
            if homework_id and student_id:
                final_stats["video_url"] = f"/get_processed_video?homework_id={homework_id}&student_id={student_id}"

        yield sse_format("final_stats", final_stats)

        # 保存视频以便下载
        download_path = os.path.join(temp_dir, "download_video.mp4")
        with open(download_path, "wb") as f:
            f.write(processed_video)

        yield sse_format("final_stats", {
            "message": "视频可供下载",
            "download_url": f"/download_processed_video?temp_id={temp_id}"
        })

        # 如果提供了保存路径和作业信息，则将处理结果保存到数据库
        if save_path and homework_id and student_id:
            try:
                video_duration = frame_index / fps if fps > 0 else 0

                # 从gym_object获取详细的反馈信息
                feedback_details = {}
                correct_count = max_count
                incorrect_count = 0

                if gym_object and hasattr(gym_object, 'result_data'):
                    result_data = gym_object.result_data
                    # 提取正确的计数和错误计数 - 这里需要修正
                    correct_count = result_data.get('correct_count', 0)  # 从tracker获取正确计数
                    incorrect_count = result_data.get('incorrect_count', 0)  # 从tracker获取错误计数

                    # 确保total_count是正确的总和
                    total_count_from_tracker = correct_count + incorrect_count

                    # 构建反馈详情
                    feedback_details = {
                        "events": result_data.get('events', []),
                        "performance": {
                            "total_count": total_count_from_tracker,  # 使用tracker的总计数
                            "correct_count": correct_count,
                            "incorrect_count": incorrect_count,
                            "accuracy_rate": correct_count / total_count_from_tracker * 100 if total_count_from_tracker > 0 else 0
                        },
                        "video_info": {
                            "total_frames": frame_index,
                            "processed_frames": processed_frame_count,
                            "fps": fps,
                            "duration": video_duration
                        }
                    }

                    # 更新max_count为tracker的总计数
                    max_count = total_count_from_tracker

                else:
                    # 默认处理方式
                    feedback_details = {
                        "processed_frame_count": processed_frame_count,
                        "max_count": max_count,
                        "performance": {
                            "total_count": max_count,
                            "correct_count": max_count,  # 默认假设全部正确
                            "incorrect_count": 0
                        }
                    }

                # 插入数据库 - 关键修改：使用tracker返回的计数
                insert_exercise_feedback(
                    homework_id=homework_id,
                    student_id=student_id,
                    pose_type=pose_type,
                    processed_video_path=save_path,
                    total_count=max_count,  # 更新后的总计数
                    correct_count=correct_count,  # 使用tracker返回的正确计数
                    incorrect_count=incorrect_count,  # 使用tracker返回的错误计数
                    feedback_json=json.dumps(feedback_details),
                    video_duration=video_duration
                )
                logger.info(
                    f"视频处理结果已保存到数据库: homework_id={homework_id}, student_id={student_id}, pose_type={pose_type}")
            except Exception as e:
                logger.error(f"保存视频处理结果到数据库时出错: {e}")
                logger.error(traceback.format_exc())

    except Exception as e:
        error_msg = f"处理视频时出错: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        yield sse_format("error", {"message": error_msg})

    finally:
        # 释放资源
        try:
            if cap is not None:
                cap.release()
            if out is not None:
                out.release()
        except Exception as e:
            logger.error(f"释放视频资源时出错: {e}")

        # 清理gym对象
        try:
            if session_id is not None and session_id in video_processor.gym_objects:
                del video_processor.gym_objects[session_id]
        except Exception as e:
            logger.error(f"清理gym对象时出错: {e}")

        # 注意：我们不立即清理temp_dir，因为用户可能需要下载视频
        # 清理将在下载完成后进行，或定期清理任务中进行


@app.post("/stream_process_video")
async def stream_process_video(file: UploadFile = File(...), pose_type: str = "pushup"):
    """流式处理视频并实时返回处理结果"""
    # 读取上传的文件内容
    file_content = await file.read()
    logger.info(f"视频文件读取完成，大小: {len(file_content)} 字节")

    return SSEStreamingResponse(stream_process_video_endpoint(file_content, pose_type))


@app.get("/download_processed_video")
async def download_processed_video(temp_id: str):
    """下载处理后的视频"""
    try:
        # 更新最后访问时间
        if temp_id in temp_dirs:
            temp_dirs[temp_id]['last_access'] = time.time()

        # 构建文件路径
        if temp_id not in temp_dirs:
            raise HTTPException(status_code=404, detail="临时目录不存在或已过期")

        temp_dir = temp_dirs[temp_id]['path']
        video_path = os.path.join(temp_dir, "download_video.mp4")

        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="视频文件不存在")

        # 返回文件响应
        return FileResponse(
            video_path,
            media_type="video/mp4",
            headers={"Content-Disposition": "attachment; filename=processed_video.mp4"}
        )
    except Exception as e:
        logger.error(f"下载视频时出错: {e}")
        raise HTTPException(status_code=500, detail="下载视频时出错")


@app.post("/process_video")
async def process_video(file: UploadFile = File(...), pose_type: str = "pushup"):
    """流式处理视频并返回处理后的完整视频"""
    # 读取上传的文件内容
    file_content = await file.read()
    logger.info(f"视频文件读取完成，大小: {len(file_content)} 字节")

    return SSEStreamingResponse(stream_process_video_endpoint(file_content, pose_type))


@app.post("/process_and_save_video")
async def process_and_save_video(
        homework_id: str = Query(..., description="作业ID"),
        student_id: str = Query(..., description="学生ID"),
        pose_type: str = Query("pushup", description="动作类型"),
        async_mode: bool = Query(False, description="为 true 时立即 202 返回并在后台跑完处理"),
        file: UploadFile = File(..., description="上传的视频文件")
):
    """流式处理视频并将处理后的视频保存到 homework/homework_id/student_id 目录下。

    - async_mode=False（默认）：返回 SSE 流，供前端实时渲染处理帧。
    - async_mode=True：把生成器塞进后台 task 跑完，立即返回 202。
      用于 PE-AI-Backend 转发场景——后端不消费 SSE 内容，只通过
      /query_records 拿结果，避免 Render→cloudflared 长连接中途超时。
    """
    # 读取上传的文件内容
    file_content = await file.read()
    logger.info(f"视频文件读取完成，大小: {len(file_content)} 字节")

    # 创建保存目录和路径（使用绝对路径）
    save_dir = os.path.join(HOMEWORK_DIR, homework_id, student_id)
    save_path = os.path.join(save_dir, "processed_video.mp4")

    # 添加日志信息
    logger.info(f"保存目录: {save_dir}")
    logger.info(f"完整路径: {os.path.abspath(save_path)}")

    if async_mode:
        async def _drain_generator():
            try:
                async for _ in stream_process_video_endpoint(
                        file_content,
                        pose_type,
                        save_path=save_path,
                        homework_id=homework_id,
                        student_id=student_id):
                    pass
            except Exception:
                logger.error("后台处理任务异常")
                logger.error(traceback.format_exc())

        asyncio.create_task(_drain_generator())
        return Response(
            status_code=202,
            content=json.dumps({
                "message": "accepted",
                "homework_id": homework_id,
                "student_id": student_id,
                "pose_type": pose_type,
            }),
            media_type="application/json",
        )

    # 使用流式处理并保存
    return SSEStreamingResponse(
        stream_process_video_endpoint(
            file_content,
            pose_type,
            save_path=save_path,
            homework_id=homework_id,
            student_id=student_id
        )
    )


@app.get("/get_processed_video")
async def get_processed_video(
        homework_id: str = Query(..., description="作业ID"),
        student_id: str = Query(..., description="学生ID"),
        download: bool = Query(False, description="是否作为附件下载")
):
    """获取已处理的视频文件 - 支持下载和流式预览"""
    video_path = os.path.join(HOMEWORK_DIR, homework_id, student_id, "processed_video.mp4")

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    # 如果是下载模式，直接返回文件
    if download:
        filename = f"processed_video_{homework_id}_{student_id}.mp4"
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Video-Info": f"homework_id={homework_id}, student_id={student_id}"
            }
        )

    # 流式预览模式 - 使用YOLO风格的SSE格式
    async def video_stream_generator():
        cap = None
        try:
            logger.info(f"开始流式传输视频: {video_path}")

            # Windows 上优先使用 MSMF 后端，避免 GStreamer 插件问题
            cap = cv2.VideoCapture(video_path, cv2.CAP_MSMF)
            if not cap.isOpened():
                # 如果 MSMF 失败，尝试默认后端
                cap.release()
                cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                # 发送错误信息
                yield sse_format("error", {"message": "无法打开视频文件"})
                return

            # 获取视频信息
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 发送视频元数据（模仿YOLO格式）
            metadata = {
                "fps": fps,
                "width": width,
                "height": height,
                "total_frames": total_frames,
                "homework_id": homework_id,
                "student_id": student_id
            }
            yield sse_format("video_info", metadata)

            frame_index = 0
            SKIP_FACTOR = 1  # 跳帧因子，减少数据传输量

            while True:
                success, frame = cap.read()
                if not success:
                    logger.info("视频流传输完成")
                    break

                # 跳帧处理，减少数据量
                if frame_index % SKIP_FACTOR != 0:
                    frame_index += 1
                    continue

                # 将帧编码为JPEG格式
                try:
                    _, buffer = cv2.imencode('.jpg', frame, [
                        cv2.IMWRITE_JPEG_QUALITY, 80  # 质量设为80%以减小文件大小
                    ])

                    if buffer is not None:
                        # 转换为base64字符串
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')

                        # YOLO风格的数据格式
                        frame_data = {
                            "frame_index": frame_index,
                            "timestamp": frame_index / fps if fps > 0 else 0,
                            "image": frame_base64  # 注意：这里使用"image"而不是"data"
                        }

                        yield sse_format("frame", frame_data)

                        # 控制发送速率
                        await asyncio.sleep(0.033)  # 约30fps

                except Exception as e:
                    logger.error(f"编码第 {frame_index} 帧时出错: {e}")
                    error_data = {
                        "message": f"编码帧错误: {str(e)}",
                        "frame": frame_index
                    }
                    yield sse_format("error", error_data)

                frame_index += 1

            # 发送完成信号
            done_data = {
                "message": "视频流传输完成",
                "total_frames_sent": frame_index
            }
            yield sse_format("complete", done_data)

        except Exception as e:
            logger.error(f"视频流传输出错: {e}")
            error_data = {
                "message": str(e)
            }
            yield sse_format("error", error_data)

        finally:
            if cap is not None:
                cap.release()

    # 返回流式响应
    return StreamingResponse(
        video_stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.delete("/delete_homework")
async def delete_homework(homework_id: str = Query(..., description="作业ID")):
    """删除指定作业ID下的所有视频文件"""
    homework_dir = os.path.join(HOMEWORK_DIR, homework_id)

    if not os.path.exists(homework_dir):
        raise HTTPException(status_code=404, detail=f"作业ID {homework_id} 不存在")

    try:
        # 删除整个作业目录及其内容
        shutil.rmtree(homework_dir)
        return {
            "status": "success",
            "message": f"作业 {homework_id} 的所有视频已成功删除"
        }
    except Exception as e:
        logger.error(f"删除作业 {homework_id} 时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除作业时出错: {str(e)}")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "model_loaded": video_processor.model is not None,
        "active_sessions": len(video_processor.gym_objects)
    }


@app.get("/supported_poses")
async def get_supported_poses():
    """获取支持的姿势类型"""
    return {
        "supported_poses": [
            "pushup", "squat", "deadlift"
        ]
    }


@app.get("/query_records")
async def query_records(
        homework_id: str = Query(..., description="作业ID"),
        student_id: str = Query(..., description="学生ID"),
        pose_type: Optional[str] = Query(None, description="动作类型")
):
    """根据作业ID、学生ID和动作类型查询反馈记录"""
    try:
        if pose_type:
            # 查询特定动作类型的记录
            result = get_exercise_feedback(homework_id, student_id, pose_type)
            if result is None:
                raise HTTPException(status_code=404, detail="未找到相关记录")
            return [result]
        else:
            # 查询该学生该作业的所有记录
            results = get_records_by_homework_student(homework_id, student_id)
            if not results:
                raise HTTPException(status_code=404, detail="未找到相关记录")
            return results
    except Exception as e:
        logger.error(f"查询记录时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/query_all_records")
async def query_all_records():
    """查询所有反馈记录"""
    try:
        return get_all_records()
    except Exception as e:
        logger.error(f"查询所有记录时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# temp_dirs 已在文件顶部定义


def cleanup_temp_dirs():
    """定期清理临时目录"""
    current_time = time.time()
    to_delete = []
    for temp_id, temp_info in temp_dirs.items():
        # 如果临时目录超过1小时未被访问，则删除
        if current_time - temp_info['last_access'] > 3600:
            try:
                shutil.rmtree(temp_info['path'])
                to_delete.append(temp_id)
            except Exception as e:
                logger.error(f"清理临时目录时出错: {e}")

    # 从字典中移除已删除的条目
    for temp_id in to_delete:
        del temp_dirs[temp_id]


@app.get("/get_record_details/{record_id}")
async def get_record_details(record_id: int):
    """获取指定记录的详细信息"""
    try:
        record = get_exercise_feedback_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        return record
    except Exception as e:
        logger.error(f"获取记录详情时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_record_details")
async def get_record_details_by_homework_student(
        homework_id: str = Query(..., description="作业ID"),
        student_id: str = Query(..., description="学生ID")
):
    """通过作业ID和学生ID获取记录的详细信息"""
    try:
        results = get_records_by_homework_student(homework_id, student_id)
        if not results:
            raise HTTPException(status_code=404, detail="未找到相关记录")
        return results
    except Exception as e:
        logger.error(f"获取记录详情时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/student/all-records/{student_id}")
async def api_get_student_all_records(student_id: str):
    """获取指定学生的所有记录（供 AIChat 服务调用）"""
    try:
        records = get_student_all_records(student_id)
        # 返回空列表而不是 404，因为新学生没有记录是正常情况
        return records if records else []
    except Exception as e:
        logger.error(f"获取学生记录时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)