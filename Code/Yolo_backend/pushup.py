"""
PushupTracker - 俯卧撑动作识别器

该模块实现了俯卧撑动作的识别、计数和姿势评估功能。

识别原理：
1. 使用 YOLOv8-pose 检测人体关键点
2. 计算肘部角度（肩-肘-腕）判断动作阶段
3. 通过状态机（s1→s2→s3→s1）识别完整动作周期
4. 检测错误姿势：背部拱起、动作幅度不足、身体下沉

关键点索引（COCO格式）：
- 6: 右肩 (right_shoulder)
- 8: 右肘 (right_elbow)
- 10: 右腕 (right_wrist)
- 12: 右髋 (right_hip)

状态机设计：
- s1: 初始阶段（手臂伸直，身体撑起）
- s2: 过渡阶段（身体下降中）
- s3: 完成阶段（胸部接近地面）
- 完整周期 s1→s2→s3→s1 计为一次有效俯卧撑
"""

import cv2
import numpy as np
from function import draw_text, calculate_angle, _show_feedback, draw_dotted_line
import time


class PushupTracker:
    """
    俯卧撑动作识别跟踪器。

    功能：
    - 检测俯卧撑动作并计数
    - 识别错误姿势并提供实时反馈
    - 记录每次动作的详细事件信息
    """

    def __init__(self):
        """初始化俯卧撑状态追踪器。"""
        # ========== 状态跟踪字典 ==========
        # 存储动作识别过程中的所有状态信息
        self.state_tracker = {
            'state_seq': [],                          # 状态序列，记录动作阶段
            'DISPLAY_TEXT': np.full((3,), False),     # 是否显示错误提示（3种错误类型）
            'COUNT_FRAMES': np.zeros((3,), dtype=np.int64),  # 错误提示显示帧数
            'INCORRECT_POSTURE': False,               # 当前是否存在错误姿势
            'curr_state': None,                       # 当前动作状态
            'PUSHUP_COUNT': 0,                        # 正确俯卧撑计数
            'IMPROPER_PUSHUP': 0,                     # 错误俯卧撑计数
            'BACK_ARCHED': False,                     # 背部拱起标志
            'INSUFFICIENT_RANGE': False,              # 动作幅度不够标志
            'BODY_SINKING': False                     # 身体下沉标志
        }

        # ========== 事件跟踪 ==========
        self.events = []                    # 存储关键事件（开始、完成、错误等）
        self.current_pushup_id = None       # 当前俯卧撑的唯一标识符
        self.pushup_start_frame = None      # 当前俯卧撑开始的帧号
        self.last_improper_count = 0        # 上次错误计数

        # ========== 错误提示映射 ==========
        # 格式：{索引: (错误代码, Y坐标位置, 颜色)}
        self.FEEDBACK_ID_MAP = {
            0: ('BACK ARCHED', 215, (255, 80, 80)),       # 背部拱起 - 红色
            1: ('INSUFFICIENT RANGE', 170, (255, 80, 80)), # 动作幅度不够 - 红色
            2: ('BODY SINKING', 125, (255, 80, 80))       # 身体下沉 - 红色
        }

        # 获取阈值配置
        self.thresholds = self.get_thresholds_beginner()

    def get_thresholds(self):
        """
        获取阈值配置。

        返回:
            dict: 阈值字典。
        """
        return self.get_thresholds_beginner()

    def get_thresholds_beginner(self):
        """
        获取初学者模式的阈值设置。

        阈值说明：
        - SHOULDER_ELBOW_WRIST: 肘部角度阈值，用于判断动作阶段
          - NORMAL (155-180°): 手臂伸直，撑起状态
          - TRANS (110-150°): 下降过渡状态
          - PASS (55-100°): 胸部接近地面，最低点
        - BACK_ARCH_ANGLE: 背部拱起角度阈值，超过此值判定为错误
        - MIN_ELBOW_ANGLE: 肘部最小角度，用于检测动作幅度
        - HIP_SHOULDER_DISTANCE_RATIO: 髋肩距离比例，用于检测身体下沉
        - INACTIVE_THRESH: 静止时间阈值（秒）
        - CNT_FRAME_THRESH: 错误提示显示帧数阈值

        返回:
            dict: 阈值配置字典
        """
        thresholds = {
            'SHOULDER_ELBOW_WRIST': {
                'NORMAL': (155, 180),  # 初始阶段（上升完成）
                'TRANS': (110, 150),   # 过渡阶段（下降中）
                'PASS': (55, 100)      # 完成阶段（下放到最低点）
            },
            'BACK_ARCH_ANGLE': 90,      # 背部拱起角度阈值（度）
            'MIN_ELBOW_ANGLE': 100,      # 肘部最小角度阈值（度）- 动作幅度不够
            'HIP_SHOULDER_DISTANCE_RATIO': 0.85,  # 髋部与肩部距离比例阈值（身体下沉）
            'INACTIVE_THRESH': 10.0,    # 静止时间阈值 (秒)
            'CNT_FRAME_THRESH': 50      # 维持帧数阈值
        }
        return thresholds

    def _get_state(self, elbow_shoulder_angle):
        """
        根据肘部角度判断动作状态。

        状态机设计：
        - s1: 初始阶段（手臂伸直，角度155-180°）
        - s2: 过渡阶段（身体下降，角度110-150°）
        - s3: 完成阶段（最低点，角度55-100°）

        参数:
            elbow_shoulder_angle: 肘部角度（度）

        返回:
            str: 状态标识（'s1', 's2', 's3'），如果不在范围内返回 None
        """
        angle = None

        # 根据肘部角度判断当前阶段
        if self.thresholds['SHOULDER_ELBOW_WRIST']['NORMAL'][0] <= elbow_shoulder_angle <= \
                self.thresholds['SHOULDER_ELBOW_WRIST']['NORMAL'][1]:
            angle = 1  # 初始阶段（上升完成）
        elif self.thresholds['SHOULDER_ELBOW_WRIST']['TRANS'][0] <= elbow_shoulder_angle <= \
                self.thresholds['SHOULDER_ELBOW_WRIST']['TRANS'][1]:
            angle = 2  # 过渡阶段（下降中）
        elif self.thresholds['SHOULDER_ELBOW_WRIST']['PASS'][0] <= elbow_shoulder_angle <= \
                self.thresholds['SHOULDER_ELBOW_WRIST']['PASS'][1]:
            angle = 3  # 完成阶段（下放到最低点）

        return f's{angle}' if angle else None

    def _update_state_sequence(self, state):
        """
        更新状态序列，根据新的状态添加到状态序列中。

        参数:
            state: 当前状态（如 's1', 's2' 等）
        """
        if state == 's2':
            # 添加状态 's2' 到状态序列
            if (('s3' not in self.state_tracker['state_seq']) and (self.state_tracker['state_seq'].count('s2')) == 0) or \
                    (('s3' in self.state_tracker['state_seq']) and (
                            self.state_tracker['state_seq'].count('s2') == 1)):
                self.state_tracker['state_seq'].append(state)

        elif state == 's3':
            # 添加状态 's3' 到状态序列
            if (state not in self.state_tracker['state_seq']) and 's2' in self.state_tracker['state_seq']:
                self.state_tracker['state_seq'].append(state)

    def _get_current_error_reasons(self):
        """获取当前错误原因，包含更多详细信息"""
        errors = []
        for i, is_displaying in enumerate(self.state_tracker['DISPLAY_TEXT']):
            if is_displaying:
                error_id, error_msg, _ = self.FEEDBACK_ID_MAP.get(i, (f"ERROR_{i}", "", (0,0,0)))
                errors.append({
                    'code': error_id,
                    'message': error_msg,
                    'frame_time': time.time(),
                    'error_type': '姿势错误，下降幅度不足，肘部角度过大'
                })
        return errors

    def _record_events(self, frame_index, fps):
        """记录关键事件，正确绑定错误信息到每个俯卧撑"""
        # 确保events列表中的每个事件都有correct_count和incorrect_count键
        if self.events:
            for event in self.events:
                if 'correct_count' not in event:
                    event['correct_count'] = self.state_tracker['PUSHUP_COUNT']
                if 'incorrect_count' not in event:
                    event['incorrect_count'] = self.state_tracker['IMPROPER_PUSHUP']

        # 检测俯卧撑开始
        if self.state_tracker['curr_state'] == 's2' and self.current_pushup_id is None:
            self.current_pushup_id = f"pushup_{len([e for e in self.events if e['type'] == 'PUSHUP_START']) + 1}"
            self.pushup_start_frame = frame_index
            self.events.append({
                'event_id': self.current_pushup_id,
                'type': 'PUSHUP_START',
                'frame': frame_index,
                'timestamp': frame_index / fps if fps > 0 else 0,
                'correct_count': self.state_tracker['PUSHUP_COUNT'],
                'incorrect_count': self.state_tracker['IMPROPER_PUSHUP'],
                'pushup_number': len([e for e in self.events if e['type'] == 'PUSHUP_START']),
                'current_errors': []
            })

        # 检查并记录当前错误
        current_errors = self._get_current_error_reasons()
        if self.current_pushup_id and current_errors:
            for event in reversed(self.events):
                if event.get('event_id') == self.current_pushup_id and event['type'] == 'PUSHUP_START':
                    for error in current_errors:
                        if error not in event.get('current_errors', []):
                            if 'current_errors' not in event:
                                event['current_errors'] = []
                            event['current_errors'].append(error)
                    break

        # 检测俯卧撑完成（正确）
        if self.current_pushup_id and self.state_tracker['curr_state'] == 's1':
            is_correct_completion = (
                len(self.state_tracker['state_seq']) == 3 and
                not self.state_tracker['INCORRECT_POSTURE']
            )

            if is_correct_completion:
                start_event = None
                for event in reversed(self.events):
                    if event.get('event_id') == self.current_pushup_id and event['type'] == 'PUSHUP_START':
                        start_event = event
                        break

                self.events.append({
                    'event_id': self.current_pushup_id,
                    'type': 'PUSHUP_COMPLETE_CORRECT',
                    'frame': frame_index,
                    'timestamp': frame_index / fps if fps > 0 else 0,
                    'duration_frames': frame_index - self.pushup_start_frame if self.pushup_start_frame else 0,
                    'correct_count': self.state_tracker['PUSHUP_COUNT'],
                    'incorrect_count': self.state_tracker['IMPROPER_PUSHUP'],
                    'pushup_number': start_event.get('pushup_number', 0) if start_event else 0,
                    'errors_during_pushup': start_event.get('current_errors', []) if start_event else []
                })
                self.current_pushup_id = None
                self.pushup_start_frame = None

            elif self.state_tracker['INCORRECT_POSTURE'] or (
                's2' in self.state_tracker['state_seq'] and
                len(self.state_tracker['state_seq']) == 1
            ):
                start_event = None
                for event in reversed(self.events):
                    if event.get('event_id') == self.current_pushup_id and event['type'] == 'PUSHUP_START':
                        start_event = event
                        break

                self.events.append({
                    'event_id': self.current_pushup_id,
                    'type': 'PUSHUP_COMPLETE_INCORRECT',
                    'frame': frame_index,
                    'timestamp': frame_index / fps if fps > 0 else 0,
                    'error_reasons': self._get_current_error_reasons(),
                    'duration_frames': frame_index - self.pushup_start_frame if self.pushup_start_frame else 0,
                    'correct_count': self.state_tracker['PUSHUP_COUNT'],
                    'incorrect_count': self.state_tracker['IMPROPER_PUSHUP'],
                    'pushup_number': start_event.get('pushup_number', 0) if start_event else 0,
                    'errors_during_pushup': start_event.get('current_errors', []) if start_event else []
                })
                self.last_improper_count = self.state_tracker['IMPROPER_PUSHUP']
                self.current_pushup_id = None
                self.pushup_start_frame = None

    def track(self, k, im0, ind, count, fps=30):
        """
        处理俯卧撑检测与计数的主逻辑。

        处理流程：
        1. 提取关键点坐标
        2. 计算肘部角度和背部角度
        3. 判断动作状态并更新状态序列
        4. 检测错误姿势
        5. 绘制骨架和反馈信息
        6. 记录事件

        参数:
            k: YOLO 检测到的关键点数据
            im0: 当前帧图像
            ind: 人物索引（单人模式为0）
            count: 计数器列表（通过引用传递更新计数）
            fps: 视频帧率

        返回:
            dict: 包含处理后的图像、计数、事件等完整结果
        """
        frame_height, frame_width, _ = im0.shape

        # ========== 第一步：提取关键点坐标 ==========
        # COCO 格式关键点索引：6=右肩, 8=右肘, 10=右腕, 12=右髋
        right_shoulder = (int(k[6][0].cpu().item()), int(k[6][1].cpu().item()))
        right_elbow = (int(k[8][0].cpu().item()), int(k[8][1].cpu().item()))
        right_wrist = (int(k[10][0].cpu().item()), int(k[10][1].cpu().item()))
        right_hip = (int(k[12][0].cpu().item()), int(k[12][1].cpu().item()))

        # ========== 第二步：绘制辅助线 ==========
        # 绘制竖直虚线作为参考线
        dotted_line_length = 60
        im0 = draw_dotted_line(im0, right_shoulder, right_shoulder[1] - dotted_line_length, right_shoulder[1], (255, 0, 0))
        im0 = draw_dotted_line(im0, right_elbow, right_elbow[1] - dotted_line_length, right_elbow[1], (255, 0, 0))
        im0 = draw_dotted_line(im0, right_wrist, right_wrist[1] - dotted_line_length, right_wrist[1], (255, 0, 0))

        # ========== 第三步：计算关键角度 ==========
        # 肘部角度（肩-肘-腕）：判断动作阶段的核心指标
        elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
        # 肘-腕角度：用于绘制角度指示器
        elbow_wrist_angle = calculate_angle(right_elbow, right_wrist)

        # 背部角度：检测背部是否拱起
        # 使用肩部和髋部连线与垂直线的夹角
        back_angle = calculate_angle(right_shoulder, right_hip, reference_direction="vertical")

        # 身体下沉检测：计算肩腕距离与髋肩距离的比例
        shoulder_wrist_distance = abs(right_shoulder[1] - right_wrist[1])
        hip_shoulder_distance = abs(right_hip[1] - right_shoulder[1])

        if hip_shoulder_distance > 0:
            body_sink_ratio = shoulder_wrist_distance / hip_shoulder_distance
        else:
            body_sink_ratio = 1.0

        # ========== 第四步：绘制骨架和关节点 ==========
        color_light_blue = (204, 204, 0)  # BGR 格式的浅蓝色
        cv2.line(im0, right_shoulder, right_elbow, color_light_blue, 4)
        cv2.line(im0, right_elbow, right_wrist, color_light_blue, 4)

        color_yellow = (0, 255, 255)  # BGR 格式的黄色
        cv2.circle(im0, right_shoulder, 7, color_yellow, -1)
        cv2.circle(im0, right_elbow, 7, color_yellow, -1)
        cv2.circle(im0, right_wrist, 7, color_yellow, -1)

        # 绘制肘部角度指示器（白色弧线）
        cv2.ellipse(im0, tuple(right_elbow), (25, 25),
                    angle=0, startAngle=elbow_wrist_angle, endAngle=elbow_wrist_angle - elbow_angle,
                    color=(255, 255, 255), thickness=3)

        # ========== 第五步：绘制计数和角度信息 ==========
        # 正确计数（绿色背景）
        draw_text(
            im0,
            "CORRECT: " + str(self.state_tracker['PUSHUP_COUNT']),
            pos=(int(frame_width * 0.68), 130),
            text_color=(255, 255, 230),
            font_scale=0.7,
            text_color_bg=(18, 185, 0)
        )

        # 错误计数（红色背景）
        draw_text(
            im0,
            "INCORRECT: " + str(self.state_tracker['IMPROPER_PUSHUP']),
            pos=(int(frame_width * 0.68), 175),
            text_color=(255, 255, 230),
            font_scale=0.7,
            text_color_bg=(221, 0, 0),
        )

        # 调试信息：显示角度值
        draw_text(
            im0,
            f"ELBOW: {round(elbow_angle, 1)}",
            pos=(int(frame_width * 0.68), 220),
            text_color=(255, 255, 255),
            font_scale=0.7,
            text_color_bg=(0, 0, 0)
        )

        draw_text(
            im0,
            f"BACK: {round(back_angle, 1)}",
            pos=(int(frame_width * 0.68), 250),
            text_color=(255, 255, 255),
            font_scale=0.7,
            text_color_bg=(0, 0, 0)
        )

        # ========== 第六步：状态判断和计数逻辑 ==========
        # 获取当前动作状态
        current_state = self._get_state(elbow_angle)
        self.state_tracker['curr_state'] = current_state
        self._update_state_sequence(current_state)

        # 计数逻辑：当回到 s1 状态时判断是否完成一次有效俯卧撑
        if current_state == 's1':
            # 完整周期 s1→s2→s3→s1 且无错误姿势 = 正确俯卧撑
            if len(self.state_tracker['state_seq']) == 3 and not self.state_tracker['INCORRECT_POSTURE']:
                self.state_tracker['PUSHUP_COUNT'] += 1
                count[0] += 1
            # 只有 s2→s1，没有到达最低点 = 动作幅度不够
            elif 's2' in self.state_tracker['state_seq'] and len(self.state_tracker['state_seq']) == 1:
                self.state_tracker['IMPROPER_PUSHUP'] += 1
                self.state_tracker['DISPLAY_TEXT'][1] = True
                self.state_tracker['INCORRECT_POSTURE'] = True
            # 存在错误姿势 = 错误俯卧撑
            elif self.state_tracker['INCORRECT_POSTURE']:
                self.state_tracker['IMPROPER_PUSHUP'] += 1

            # 重置状态
            self.state_tracker['state_seq'] = []
            self.state_tracker['INCORRECT_POSTURE'] = False

        # ========== 第七步：错误姿势检测 ==========
        else:
            # 重置错误显示标志
            self.state_tracker['DISPLAY_TEXT'][:] = False

            # 检测背部拱起：背部角度超过阈值
            if abs(back_angle) > self.thresholds['BACK_ARCH_ANGLE']:
                self.state_tracker['DISPLAY_TEXT'][0] = True
                self.state_tracker['INCORRECT_POSTURE'] = True

            # 检测身体下沉：髋肩距离比例过低
            elif body_sink_ratio < self.thresholds['HIP_SHOULDER_DISTANCE_RATIO']:
                self.state_tracker['DISPLAY_TEXT'][2] = True
                self.state_tracker['INCORRECT_POSTURE'] = True

            # 更新错误显示帧数
            self.state_tracker['COUNT_FRAMES'][self.state_tracker['DISPLAY_TEXT']] += 1

            # 显示错误提示
            im0 = _show_feedback(im0, self.state_tracker['COUNT_FRAMES'], self.FEEDBACK_ID_MAP)

        # ========== 第八步：重置和清理 ==========
        # 重置超过显示帧数阈值的错误提示
        self.state_tracker['DISPLAY_TEXT'][self.state_tracker['COUNT_FRAMES'] > self.thresholds['CNT_FRAME_THRESH']] = False
        self.state_tracker['COUNT_FRAMES'][self.state_tracker['COUNT_FRAMES'] > self.thresholds['CNT_FRAME_THRESH']] = 0

        # 记录事件（开始、完成等）
        self._record_events(count[0], fps)

        # ========== 返回完整结果 ==========
        result_data = {
            'processed_frame': im0,                                              # 处理后的图像帧
            'correct_count': self.state_tracker['PUSHUP_COUNT'],                 # 正确计数
            'incorrect_count': self.state_tracker['IMPROPER_PUSHUP'],            # 错误计数
            'total_count': self.state_tracker['PUSHUP_COUNT'] + self.state_tracker['IMPROPER_PUSHUP'],  # 总计数
            'events': self.events[-10:] if self.events else [],                  # 最近10个事件
        }

        return result_data
