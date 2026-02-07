"""物理工具函数模块。

该模块提供计算各种形状转动惯量的便利函数，用于配置Pymunk刚体的物理属性。
"""

from pymunk import (
    moment_for_box,
    moment_for_circle,
    moment_for_poly,
    moment_for_segment,
)


def get_moment_for_box(mass: float, width: float, height: float) -> float:
    """计算矩形形状的转动惯量。
    
    基于矩形的质量、宽度和高度计算绕中心的转动惯量。
    
    Args:
        mass (float): 矩形的质量。
        width (float): 矩形的宽度。
        height (float): 矩形的高度。
    
    Returns:
        float: 转动惯量值。
    """
    return moment_for_box(mass=mass, size=(width, height))


def get_moment_for_circle(
    mass: float,
    inner_radius: float,
    outer_radius: float,
    x_offset: float = 0,
    y_offset: float = 0,
) -> float:
    """计算圆环/圆形的转动惯量。
    
    基于圆环的质量、内外半径和偏移量计算转动惯量。
    当内半径为0时，计算实心圆的转动惯量。
    
    Args:
        mass (float): 圆环的质量。
        inner_radius (float): 内半径。
        outer_radius (float): 外半径。
        x_offset (float, optional): 中心X偏移，默认为0。
        y_offset (float, optional): 中心Y偏移，默认为0。
    
    Returns:
        float: 转动惯量值。
    """
    return moment_for_circle(
        mass=mass,
        inner_radius=inner_radius,
        outer_radius=outer_radius,
        offset=(x_offset, y_offset),
    )


def get_moment_for_poly(
    mass: float,
    vertices: list[tuple[float, float]],
    x_offset: float = 0,
    y_offset: float = 0,
    stroke_width: float = 0,
) -> float:
    """计算多边形的转动惯量。
    
    基于多边形的质量、顶点坐标和偏移量计算转动惯量。
    
    Args:
        mass (float): 多边形的质量。
        vertices (list[tuple[float, float]]): 多边形顶点列表，每个顶点为(x, y)坐标。
        x_offset (float, optional): 中心X偏移，默认为0。
        y_offset (float, optional): 中心Y偏移，默认为0。
        stroke_width (float, optional): 形状的半径（用于线宽），默认为0。
    
    Returns:
        float: 转动惯量值。
    """
    return moment_for_poly(
        mass=mass, vertices=vertices, offset=(x_offset, y_offset), radius=stroke_width
    )


def get_moment_for_line(
    mass: float,
    start: tuple[float, float],
    end: tuple[float, float],
    stroke_width: float,
) -> float:
    """计算线段的转动惯量。
    
    基于线段的质量、端点和宽度计算转动惯量。
    
    Args:
        mass (float): 线段的质量。
        start (tuple[float, float]): 线段起点坐标(x, y)。
        end (tuple[float, float]): 线段终点坐标(x, y)。
        stroke_width (float): 线段的宽度（半径）。
    
    Returns:
        float: 转动惯量值。
    """
    return moment_for_segment(mass=mass, a=start, b=end, radius=stroke_width)

