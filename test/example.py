import pymunk
from pymunk.autogeometry import march_soft, simplify_vertexes, convex_decomposition
from PIL import Image, ImageFilter
import numpy as np


def get_normalized_convex_polygons(pixel_array, base_width=256.0, target_cell_size=4):
    # 1. 获取原图尺寸并缩放
    orig_h, orig_w = pixel_array.shape[:2]
    actual_base_width = min(base_width, orig_w)
    scale_factor = orig_w / actual_base_width
    actual_base_height = int(orig_h / scale_factor)

    # 2. 预处理：转灰度并进行【对比度自动拉伸】
    # 这一步非常关键！它能强行拉开暗色子弹与黑背景的距离
    from PIL import ImageOps
    img_obj = Image.fromarray(pixel_array.astype('uint8')).convert('L')
    img_obj = ImageOps.autocontrast(img_obj, cutoff=0.5) # 忽略1%的极值，拉伸剩余色阶
    
    img_resized = img_obj.resize((int(actual_base_width), actual_base_height), Image.Resampling.LANCZOS)
    img_np = np.array(img_resized)

    # === 【核心修改：环形全边缘背景采样】 ===
    # 提取四周所有像素点来锁定背景色
    top_edge = img_np[0, :]
    bottom_edge = img_np[-1, :]
    left_edge = img_np[:, 0]
    right_edge = img_np[:, -1]
    border_pixels = np.concatenate([top_edge, bottom_edge, left_edge, right_edge])
    
    # 获取背景色的统计特征
    bg_color = np.median(border_pixels)
    bg_std = np.std(border_pixels) # 背景噪声水平
    
    # 计算每个像素与背景的差异
    diff = np.abs(img_np.astype(np.int16) - bg_color)
    
    # 动态设定阈值：如果背景很纯净(std小)，阈值可以更低以捕捉暗部细节
    # 容差设为背景波动的 3 倍，但不低于 15
    dynamic_threshold = max(10, bg_std * 3)
    
    mask_np = np.where(diff > dynamic_threshold, 255, 0).astype(np.uint8)
    mask = Image.fromarray(mask_np)
    
    # 闭运算修复：填充金属高光导致的断裂
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))

    # 3. 采样探测
    def sample_func(point):
        x, y = int(point[0]), int(point[1])
        if 0 <= x < actual_base_width and 0 <= y < actual_base_height:
            return mask.getpixel((x, y))
        return 0

    bb = pymunk.BB(0, 0, actual_base_width - 1, actual_base_height - 1)
    x_samples = max(20, int(actual_base_width / target_cell_size))
    y_samples = max(20, int(actual_base_height / target_cell_size))
    
    pl_set = march_soft(bb, x_samples, y_samples, 128.0, sample_func)

    # 4. 顶点映射还原
    final_polygons = []
    for polyline in pl_set:
        simplified = simplify_vertexes(polyline, 0.4) 
        if len(simplified) > 3:
            try:
                parts = convex_decomposition(simplified, 0.1)
                for part in parts:
                    final_polygons.append([(p[0] * scale_factor, p[1] * scale_factor) for p in part])
            except: continue
                
    return final_polygons


from manim import *

# 使用示例
img = ImageMobject(filename_or_array=r"test_2.png").scale(0.5)
polygons = get_normalized_convex_polygons(img.pixel_array)
print(f"生成了 {len(polygons)} 个凸多边形")


import matplotlib.pyplot as plt
import matplotlib.patches as patches


def visualize_results(original_img_array, convex_polygons):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

    # 1. 显示原图
    ax1.imshow(original_img_array)
    ax1.set_title(f"Original Image", fontsize=15)
    ax1.axis("off")

    # 2. 显示生成的多边形
    # 设置背景颜色以便观察深色形状
    ax2.set_facecolor("#f0f0f0")

    h, w = original_img_array.shape[:2]

    for poly in convex_polygons:
        # Pymunk 的顶点通常是 Vec2d 对象，转换为 numpy 数组
        # 注意：如果图像显示颠倒，可以将 y 坐标修改为 h - y
        pts = np.array([(p[0], p[1]) for p in poly])

        # 随机颜色让 552 个多边形边界清晰
        color = np.random.rand(
            3,
        )
        polygon_patch = patches.Polygon(
            pts,
            closed=True,
            linewidth=0.5,
            edgecolor="black",
            facecolor=color,
            alpha=0.7,
        )
        ax2.add_patch(polygon_patch)

    # 设置绘图范围与原图一致
    ax2.set_xlim(0, w)
    ax2.set_ylim(h, 0)  # 翻转 y 轴以匹配图像坐标系
    ax2.set_aspect("equal")
    ax2.set_title(f"Generated {len(convex_polygons)} Convex Polygons", fontsize=15)
    ax2.axis("off")

    plt.tight_layout()
    plt.show()


# 调用显示函数
# 假设你的原图数组是 img.pixel_array
visualize_results(img.pixel_array, polygons)
