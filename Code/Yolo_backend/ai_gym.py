"""
AIGym - 健身动作识别核心协调类

该模块是 YOLO 视频处理服务的核心组件，负责：
1. 加载和管理 YOLOv8-pose 姿态估计模型
2. 协调不同运动类型的 Tracker（俯卧撑、深蹲、硬拉）
3. 处理视频帧并返回动作计数和反馈结果

架构设计：
- AIGym 作为协调者，不直接实现动作识别逻辑
- 具体的动作识别由各个 Tracker 类实现（PushupTracker、SquatTracker、DeadliftTracker）
- 采用策略模式，通过 pose_type 参数选择不同的 Tracker

使用示例：
    gym = AIGym(kpts_to_check=[6, 8, 10], pose_type="pushup")
    processed_frame, count = gym.monitor(frame)
"""

import cv2
import os
import logging
import numpy as np
from ultralytics.solutions.solutions import BaseSolution
from ultralytics.utils.plotting import Annotator
from function import calculate_angle
import traceback

# 导入各运动类型的跟踪器类
try:
    from squat import SquatTracker
    from deadlift import DeadliftTracker
    from pushup import PushupTracker
except ImportError as e:
    logging.error(f"无法导入跟踪器模块: {e}")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= 路径配置 =================
# 获取当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")

# 默认模型路径（按优先级）
DEFAULT_MODEL_PATHS = [
    os.path.join(SCRIPT_DIR, "yolov8n-pose.pt"),
    os.path.join(MODELS_DIR, "yolov8n-pose.pt"),
    "yolov8n-pose.pt",  # 回退到 ultralytics 默认下载路径
]


def _find_model_path():
    """查找可用的模型路径。"""
    for path in DEFAULT_MODEL_PATHS:
        if os.path.exists(path):
            return path
    # 如果都不存在，返回默认名称（ultralytics 会自动下载）
    return "yolov8n-pose.pt"


class AIGym(BaseSolution):
    def __init__(self, kpts_to_check, line_thickness=2, pose_type="pushup",
                 **kwargs):
        """
        初始化 AIGym 健身动作识别器。

        参数:
            kpts_to_check: 用于角度计算的关键点索引列表
                - 俯卧撑: [6, 8, 10] (右肩-右肘-右腕)
                - 深蹲: [12, 14, 16] (右髋-右膝-右踝)
                - 硬拉: [6, 12, 14] (右肩-右髋-右膝)
            line_thickness: 绘制骨架线的粗细，默认为2
            pose_type: 动作类型，支持 "pushup"、"squat"、"deadlift"
            **kwargs: 其他传递给 BaseSolution 的参数
        """
        # 确保使用姿态估计模型（而非普通检测模型）
        # 使用绝对路径查找模型
        if "model" not in kwargs:
            kwargs["model"] = _find_model_path()
        elif "model" in kwargs and "-pose" not in kwargs["model"]:
            kwargs["model"] = _find_model_path()

        # 初始化基础属性
        self.im0 = None                    # 当前处理的图像帧
        self.tf = line_thickness           # 线条粗细
        self.keypoints = None              # 检测到的关键点
        self.threshold = 0.001             # 关键点置信度阈值
        self.angle = None                  # 当前角度值
        self.count = None                  # 动作计数
        self.stage = None                  # 动作阶段
        self.pose_type = pose_type         # 动作类型
        self.annotator = None              # 图像标注器
        self.fps = 30                      # 视频帧率
        self.result_data = {}              # 存储完整的处理结果数据

        # 调用父类初始化
        super().__init__(**kwargs)

        # 初始化计数和状态
        self.count = 0
        self.angle = 0
        self.stage = "-"

        # 从配置文件读取角度阈值
        # up_angle: 动作"向上"阶段的角度阈值（如俯卧撑撑起时）
        # down_angle: 动作"向下"阶段的角度阈值（如俯卧撑下压时）
        self.initial_stage = None
        self.poseup_angle = float(self.CFG["up_angle"])
        self.posedown_angle = float(self.CFG["down_angle"])
        self.kpts = kpts_to_check          # 用户指定的关键点索引
        self.lw = line_thickness

        # 根据动作类型实例化对应的 Tracker
        # 采用策略模式，不同运动使用不同的识别算法
        if pose_type == "squat":
            self.tracker = SquatTracker()
        elif pose_type == "deadlift":
            self.tracker = DeadliftTracker()
        elif pose_type == "pushup":
            self.tracker = PushupTracker()
        else:
            logger.warning(f"不支持的动作类型: {pose_type}，使用默认跟踪器")
            self.tracker = PushupTracker()

        # 从 Tracker 获取共享属性和方法
        self._get_state = self.tracker._get_state
        self.state_tracker = self.tracker.state_tracker
        self._update_state_sequence = self.tracker._update_state_sequence
        self.thresholds = self.tracker.thresholds
        self.FEEDBACK_ID_MAP = self.tracker.FEEDBACK_ID_MAP

    @staticmethod
    def _point_xy(point):
        point_array = np.asarray(point[:2], dtype=float)
        return int(point_array[0]), int(point_array[1])

    def _estimate_pose_angle(self, *kpts):
        return calculate_angle(*[np.asarray(kpt[:2], dtype=float) for kpt in kpts])

    def _draw_specific_points(self, im0, keypoints, keypoint_indices, radius):
        points = []
        for idx in keypoint_indices:
            if int(idx) >= len(keypoints):
                continue
            x, y = self._point_xy(keypoints[int(idx)])
            points.append((x, y))
            cv2.circle(im0, (x, y), radius, (0, 255, 255), -1)

        for start, end in zip(points, points[1:]):
            cv2.line(im0, start, end, (0, 255, 255), max(1, self.lw))

        return im0

    def monitor(self, im0):
        """
        处理单帧图像，进行姿态估计和动作识别。

        这是 AIGym 的核心方法，处理流程：
        1. 使用 YOLO 模型检测人体姿态关键点
        2. 计算指定关键点的角度
        3. 调用对应 Tracker 进行动作识别和计数
        4. 在图像上绘制骨架和反馈信息

        参数:
            im0: 输入的 BGR 格式图像帧

        返回:
            tuple: (处理后的图像帧, 当前动作计数)
        """
        # ========== 第一步：YOLO 模型姿态检测 ==========
        try:
            logger.debug("开始YOLO模型跟踪处理...")
            frame_copy = im0.copy()  # 复制帧避免资源冲突
            logger.debug("帧复制完成")

            # 调用 YOLO 模型进行姿态跟踪
            # persist=True 启用跟踪持久化，提高跨帧一致性
            tracks = self.model.track(source=frame_copy, persist=True, classes=self.CFG["classes"])[0]
            logger.debug("YOLO模型跟踪完成")
        except Exception as e:
            error_msg = f"模型跟踪错误: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return im0, 0

        # 检查是否检测到人体
        if not tracks or len(tracks) == 0:
            logger.info("当前帧未检测到人体")
            return im0, 0

        # ========== 第二步：处理检测结果 ==========
        if tracks.boxes.id is not None:
            # 初始化图像标注器
            self.annotator = Annotator(im0, line_width=self.lw)

            # 只处理第一个检测到的人物（单人模式）
            k = tracks.keypoints.data[0]

            # 计算关键点角度
            try:
                # 提取指定的关键点坐标
                kpts = [k[int(self.kpts[i])].cpu() for i in range(3)]
                # 估计姿态角度
                self.angle = self._estimate_pose_angle(*kpts)
                # 绘制关键点
                im0 = self._draw_specific_points(im0, k, self.kpts, radius=self.lw * 3)
            except Exception as e:
                logger.error(f"关键点处理错误: {e}")
                logger.error(traceback.format_exc())

            # ========== 第三步：调用 Tracker 进行动作识别 ==========
            if self.pose_type in {"deadlift", "pushup", "squat"}:
                try:
                    # 创建计数器列表（通过列表传递实现引用传递）
                    count_list = [self.count]

                    # 调用 Tracker 的 track 方法进行动作识别
                    # 参数：关键点数据、图像帧、索引（单人模式为0）、计数器、帧率
                    tracker_result = self.tracker.track(k, im0, 0, count_list, fps=self.fps)

                    # 处理返回结果
                    if isinstance(tracker_result, dict):
                        # 新版本返回字典，包含完整的处理结果
                        im0 = tracker_result.get('processed_frame', im0)
                        self.result_data = tracker_result
                    else:
                        # 向后兼容：直接返回图像
                        im0 = tracker_result
                        self.result_data = {
                            'processed_frame': im0,
                            'correct_count': self.count,
                            'incorrect_count': 0,
                            'events': []
                        }

                    # 更新计数器
                    self.count = count_list[0]

                except Exception as e:
                    logger.error(f"动作跟踪错误 [{self.pose_type}]: {e}")
                    logger.error(traceback.format_exc())
                    self.result_data = {
                        'processed_frame': im0,
                        'correct_count': self.count,
                        'incorrect_count': 0,
                        'events': []
                    }

        # 绘制关键点连线
        if hasattr(self.annotator, 'kpts'):
            self.annotator.kpts(k, shape=(640, 640), radius=1, kpt_line=True)

        return im0, self.count
