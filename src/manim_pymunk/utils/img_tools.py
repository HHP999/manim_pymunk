"""图片工具模块。

该模块提供将图片转换为Pymunk物理形状的工具函数，支持透明背景图和实色背景图的智能处理。
"""

import pymunk
from pymunk.autogeometry import march_soft, simplify_vertexes, convex_decomposition
from PIL import Image, ImageFilter, ImageOps
import numpy as np


def get_normalized_convex_polygons(
    pixel_array, base_width=512.0, target_cell_size=4, frame_w=8, frame_h=14.22
):
    """从像素数组中提取规范化的凸多边形集合。
    
    该函数通过marchingSquares算法和凸分解，从图片中智能提取
    碰撞用的凸多边形。支持透明背景和实色背景的自动识别。
    
    Args:
        pixel_array (np.ndarray): 输入图片的像素数组[H, W, C]。
        base_width (float, optional): 采样基准宽度，默认为512.0。
            用于控制采样精度。
        target_cell_size (float, optional): 目标单元格大小，默认为4。
            控制marchingSquares的网格密度。
        frame_w (float, optional): Manim框架宽度，默认为8。
            用于坐标映射。
        frame_h (float, optional): Manim框架高度，默认为14.22。
            用于坐标映射。
    
    Returns:
        list: Manim坐标系中的凸多边形列表，每个多边形为顶点坐标列表。
    """
    # 1. 基础维度获取
    orig_h, orig_w = pixel_array.shape[:2]
    is_rgba = pixel_array.shape[2] == 4 if len(pixel_array.shape) > 2 else False

    actual_base_width = min(base_width, orig_w)
    scale_factor = orig_w / actual_base_width
    actual_base_height = int(orig_h / scale_factor)

    # 2. 智能判断：这是"透明背景图"还是"带Alpha通道的实色图"？
    use_alpha_mask = False
    if is_rgba:
        alpha_channel = pixel_array[:, :, 3]
        # 计算透明像素占比：如果透明像素超过 1%，通常认为它是抠好图的透明背景
        transparent_ratio = np.mean(alpha_channel < 32)
        if transparent_ratio > 0.1:
            use_alpha_mask = True

    # 3. 根据判断结果生成 Mask
    if use_alpha_mask:
        # --- 路径 A: 透明背景处理 ---
        # 直接使用 Alpha 通道，这比任何颜色分析都准
        img_obj = Image.fromarray(pixel_array[:, :, 3]).convert("L")
        img_resized = img_obj.resize(
            (int(actual_base_width), actual_base_height), Image.Resampling.LANCZOS
        )
        mask_np = np.where(np.array(img_resized) > 128, 255, 0).astype(np.uint8)
    else:
        # --- 路径 B: 实色背景处理 (保留你原有的对比度拉伸逻辑) ---
        img_rgb = Image.fromarray(pixel_array[:, :, :3].astype("uint8")).convert("L")
        img_obj = ImageOps.autocontrast(img_rgb, cutoff=0.5)
        img_resized = img_obj.resize(
            (int(actual_base_width), actual_base_height), Image.Resampling.LANCZOS
        )
        img_np = np.array(img_resized)

        # 环形边缘采样逻辑
        border_pixels = np.concatenate(
            [img_np[0, :], img_np[-1, :], img_np[:, 0], img_np[:, -1]]
        )
        bg_color = np.median(border_pixels)
        bg_std = np.std(border_pixels)
        diff = np.abs(img_np.astype(np.int16) - bg_color)
        dynamic_threshold = max(10, bg_std * 3)
        mask_np = np.where(diff > dynamic_threshold, 255, 0).astype(np.uint8)

    # 4. 后处理与采样
    mask = Image.fromarray(mask_np)
    # 闭运算：连接断裂的高光位
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))

    def sample_func(point):
        """采样函数：根据坐标返回Mask值。
        
        Args:
            point (tuple): (x, y)坐标。
        
        Returns:
            int: 该点的Mask值（0或255）。
        """
        x, y = int(point[0]), int(point[1])
        if 0 <= x < actual_base_width and 0 <= y < actual_base_height:
            return mask.getpixel((x, y))
        return 0

    bb = pymunk.BB(0, 0, actual_base_width - 1, actual_base_height - 1)
    x_samples = max(20, int(actual_base_width / target_cell_size))
    y_samples = max(20, int(actual_base_height / target_cell_size))

    pl_set = march_soft(bb, x_samples, y_samples, 128.0, sample_func)

    # 4. 顶点映射还原
    pixel_polygons = []
    for polyline in pl_set:
        simplified = simplify_vertexes(polyline, 0.4)
        if len(simplified) > 3:
            try:
                parts = convex_decomposition(simplified, 0.1)
                for part in parts:
                    pixel_polygons.append(
                        [(p[0] * scale_factor, p[1] * scale_factor) for p in part]
                    )
            except:
                continue
    
    # 坐标转换
    manim_polygons = map_polygons_to_manim(
        pixel_polygons,
        img_w=orig_w,
        img_h=orig_h,
        frame_w=frame_w,
        frame_h=frame_h,
    )
    return manim_polygons


def map_polygons_to_manim(polygons, img_w, img_h, frame_w, frame_h):
    """将像素坐标系中的多边形映射到Manim坐标系。
    
    执行坐标系转换：从图片像素坐标转换为Manim的笛卡尔坐标系。
    
    Args:
        polygons (list): 像素坐标系中的多边形列表。
        img_w (float): 图片宽度（像素）。
        img_h (float): 图片高度（像素）。
        frame_w (float): Manim框架宽度。
        frame_h (float): Manim框架高度。
    
    Returns:
        list: Manim坐标系中的多边形列表。
    """
    manim_polygons = []
    for poly in polygons:
        manim_vertices = []
        for x, y in poly:
            # 执行坐标映射
            m_x = (x / img_w - 0.5) * frame_w
            m_y = (0.5 - y / img_h) * frame_h
            manim_vertices.append([m_x, m_y])
        manim_polygons.append(manim_vertices)
    return manim_polygons
