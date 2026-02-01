from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Tuple, Union

import pymunk


@dataclass
class BodyConfig:
    """专门负责 pymunk.Body 属性的配置"""

    # 刚体类型: DYNAMIC, KINEMATIC, STATIC
    body_type: int = pymunk.Body.DYNAMIC

    # 基础物理量 (通常由 Shape 密度自动计算，但允许手动覆盖)
    mass: float = 0.0
    moment: float = 0.0
    center_of_gravity: Tuple[float, float] = (0.0, 0.0)

    # 初始空间状态
    # position 为 None 时默认使用 Manim 对象的 get_center(),,用户不应该使用这两个属性
    position: Optional[Tuple[float, float]] = None
    angle: float = 0.0

    # 初始运动状态
    velocity: Tuple[float, float] = (0.0, 0.0)
    angular_velocity: float = 0.0

    # 受力状态 (虽然每帧会重置，但可以设置初始力)
    force: Tuple[float, float] = (0.0, 0.0)
    torque: float = 0.0

