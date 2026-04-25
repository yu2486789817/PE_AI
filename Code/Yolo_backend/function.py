"""
function.py - 辅助绘图和计算函数

该模块提供动作识别所需的辅助功能：
1. 图像绘制函数：圆角矩形、文本、虚线等
2. 角度计算函数：三点夹角、两点与参考方向夹角
3. 反馈显示函数：在图像上显示错误提示

所有函数都针对 OpenCV BGR 格式图像设计。
"""

import cv2
import numpy as np


def draw_rounded_rect(img, rect_start, rect_end, corner_width, box_color):
    """
    绘制圆角矩形。

    通过组合矩形和椭圆来绘制圆角矩形，用于显示文本背景。

    参数:
        img: 输入图像
        rect_start: 矩形左上角坐标 (x1, y1)
        rect_end: 矩形右下角坐标 (x2, y2)
        corner_width: 圆角半径
        box_color: 填充颜色 (B, G, R)

    返回:
        img: 绘制后的图像
    """
    x1, y1 = rect_start
    x2, y2 = rect_end
    w = corner_width

    # 绘制填充矩形（四边和中心）
    cv2.rectangle(img, (x1 + w, y1), (x2 - w, y1 + w), box_color, -1)
    cv2.rectangle(img, (x1 + w, y2 - w), (x2 - w, y2), box_color, -1)
    cv2.rectangle(img, (x1, y1 + w), (x1 + w, y2 - w), box_color, -1)
    cv2.rectangle(img, (x2 - w, y1 + w), (x2, y2 - w), box_color, -1)
    cv2.rectangle(img, (x1 + w, y1 + w), (x2 - w, y2 - w), box_color, -1)

    # 绘制四个圆角（填充椭圆）
    cv2.ellipse(img, (x1 + w, y1 + w), (w, w),
                angle=0, startAngle=-90, endAngle=-180, color=box_color, thickness=-1)
    cv2.ellipse(img, (x2 - w, y1 + w), (w, w),
                angle=0, startAngle=0, endAngle=-90, color=box_color, thickness=-1)
    cv2.ellipse(img, (x1 + w, y2 - w), (w, w),
                angle=0, startAngle=90, endAngle=180, color=box_color, thickness=-1)
    cv2.ellipse(img, (x2 - w, y2 - w), (w, w),
                angle=0, startAngle=0, endAngle=90, color=box_color, thickness=-1)

    return img


def draw_text(
        img,
        msg,
        width=8,
        font=cv2.FONT_HERSHEY_SIMPLEX,
        pos=(0, 0),
        font_scale=1,
        font_thickness=2,
        text_color=(0, 255, 0),
        text_color_bg=(0, 0, 0),
        box_offset=(20, 10),
):
    """
    在图像上绘制带圆角背景的文本。

    参数:
        img: 输入图像
        msg: 要显示的文本字符串
        width: 圆角宽度
        font: 字体类型
        pos: 文本位置 (x, y)
        font_scale: 字体缩放比例
        font_thickness: 字体粗细
        text_color: 文本颜色 (B, G, R)
        text_color_bg: 背景颜色 (B, G, R)
        box_offset: 背景框偏移量 (水平, 垂直)

    返回:
        text_size: 文本尺寸 (width, height)
    """
    offset = box_offset
    x, y = pos
    text_size, _ = cv2.getTextSize(msg, font, font_scale, font_thickness)
    text_w, text_h = text_size
    rec_start = tuple(p - o for p, o in zip(pos, offset))
    rec_end = tuple(m + n - o for m, n, o in zip((x + text_w, y + text_h), offset, (25, 0)))

    # 绘制圆角背景
    img = draw_rounded_rect(img, rec_start, rec_end, width, text_color_bg)

    # 绘制文本
    cv2.putText(
        img,
        msg,
        (int(rec_start[0] + 6), int(y + text_h + font_scale - 1)),
        font,
        font_scale,
        text_color,
        font_thickness,
        cv2.LINE_AA,
    )

    return text_size


def _show_feedback(frame, c_frame, dict_maps):
    """
    在图像上显示错误反馈提示。

    根据错误状态数组，在对应位置显示错误提示文本。

    参数:
        frame: 当前图像帧
        c_frame: 错误状态的布尔数组（True 表示显示对应错误）
        dict_maps: 错误提示映射字典
            格式：{索引: (错误文本, Y坐标位置, 颜色)}

    返回:
        frame: 添加了反馈信息的图像帧
    """
    for idx in np.where(c_frame)[0]:
        draw_text(frame, dict_maps[idx][0], pos=(30, dict_maps[idx][1]), text_color=(255, 255, 230),
                  font_scale=0.6,
                  text_color_bg=dict_maps[idx][2])
    return frame


def calculate_angle(point1, point2, point3=None, reference_direction='horizontal'):
    """
    计算角度的通用函数。

    支持两种计算模式：
    1. 三点夹角：计算 point1-point2-point3 形成的夹角
    2. 两点与参考方向夹角：计算 point1-point2 连线与参考方向的夹角

    参数:
        point1: 第一个关键点的坐标 (x1, y1)
        point2: 第二个关键点的坐标 (x2, y2)
        point3: (可选) 第三个关键点的坐标 (x3, y3)
        reference_direction: 参考方向，'horizontal'（水平）或 'vertical'（竖直）

    返回:
        float: 角度值（单位为度）

    示例:
        # 计算肘部角度（肩-肘-腕）
        elbow_angle = calculate_angle(shoulder, elbow, wrist)

        # 计算手臂与垂直方向的夹角
        arm_vertical_angle = calculate_angle(shoulder, elbow, reference_direction="vertical")
    """
    point1 = np.asarray(point1)
    point2 = np.asarray(point2)

    # 三点夹角计算
    if point3 is not None:
        point3 = np.asarray(point3)

        # 创建向量：从 point2 指向 point1 和 point3
        vector1 = point1 - point2
        vector2 = point3 - point2

        # 计算向量间的夹角
        cosine_angle = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
        # 限制范围，避免浮点精度导致 NaN
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        angle = np.arccos(cosine_angle)
        angle_degrees = np.degrees(angle)

        return angle_degrees

    # 两点与参考方向夹角计算
    else:
        delta_y = point2[1] - point1[1]
        delta_x = point2[0] - point1[0]

        # 计算连线与水平面的夹角
        angle = np.arctan2(abs(delta_y), abs(delta_x))
        angle_degrees = np.degrees(angle)

        if reference_direction == 'horizontal':
            angle = angle_degrees
        elif reference_direction == 'vertical':
            angle = 90 - angle_degrees  # 转换为与竖直方向的夹角

        return angle


def find_angle(p1, p2, ref_pt=np.array([0, 1])):
    """
    计算两点连线与参考向量的夹角。

    参数:
        p1: 第一个点坐标
        p2: 第二个点坐标
        ref_pt: 参考向量，默认为 (0, 1) 即竖直向下

    返回:
        int: 夹角（整数度数）
    """
    # 计算向量
    vector_p1p2 = p2[:2] - p1[:2]
    # 计算夹角
    cos_theta = np.dot(vector_p1p2, ref_pt) / (np.linalg.norm(vector_p1p2) * np.linalg.norm(ref_pt))
    # 限制范围
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    theta = np.arccos(cos_theta)
    degree = np.degrees(theta)
    return int(degree)


def draw_dotted_line(frame, lm_coord, start, end, line_color):
    """
    绘制竖直虚线。

    用于在图像上绘制参考线，帮助可视化关键点位置。

    参数:
        frame: 输入图像
        lm_coord: 关键点坐标 (x, y)，虚线的 X 坐标
        start: 虚线起始 Y 坐标
        end: 虚线结束 Y 坐标
        line_color: 虚线颜色 (B, G, R)

    返回:
        frame: 绘制后的图像
    """
    pix_step = 0

    # 每隔 8 像素绘制一个点，形成虚线效果
    for i in range(start, end + 1, 8):
        cv2.circle(frame, (lm_coord[0], i + pix_step), 2, line_color, -1, lineType=cv2.LINE_AA)

    return frame