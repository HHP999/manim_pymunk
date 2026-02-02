from pymunk import (
    moment_for_box,
    moment_for_circle,
    moment_for_poly,
    moment_for_segment,
)


# 获取矩形惯量
def get_moment_for_box(mass: float, width: float, height: float) -> float:
    return moment_for_box(mass=mass, size=(width, height))


# 获取圆环/形惯量
def get_moment_for_circle(
    mass: float,
    inner_radius: float,
    outer_radius: float,
    x_offset: float = 0,
    y_offset: float = 0,
) -> float:
    return moment_for_circle(
        mass=mass,
        inner_radius=inner_radius,
        outer_radius=outer_radius,
        offset=(x_offset, y_offset),
    )


# 获取多边形惯量
def get_moment_for_poly(
    mass: float,
    vertices: list[tuple[float, float]], #顶点列表
    x_offset: float = 0,
    y_offset: float = 0,
    stroke_width: float = 0,
) -> float:
    return moment_for_poly(
        mass=mass, vertices=vertices, offset=(x_offset, y_offset), radius=stroke_width
    )


# 获取线段惯量
def get_moment_for_line(
    mass: float,
    start: tuple[float, float],
    end: tuple[float, float],
    stroke_width: float,
) -> float:
    return moment_for_segment(mass=mass, a=start, b=end, radius=stroke_width)
