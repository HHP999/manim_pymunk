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


@dataclass
class ShapeConfig:
    """专门负责 pymunk.Shape 碰撞与材质属性的配置"""

    # --- 1. 物理材质 (最常用) ---
    # 弹性: 0.0 不弹, 1.0 完美反弹
    elasticity: float = 0.8
    # 摩擦力: 0.0 无摩擦, >1.0 也是合法的
    friction: float = 0.8

    # --- 2. 质量分配 (核心设计) ---
    # 推荐使用 density。如果设置了密度，mass 会根据形状面积自动计算
    density: float = 1.0
    # 如果手动设置了 mass，它会覆盖 density 的计算结果
    mass: Optional[float] = None

    # --- 3. 碰撞过滤与识别 ---
    # collision_type: 用于回调函数的类型标记 (int)
    collision_type: int = 0
    # # filter: 控制哪些物体可以相撞，哪些直接穿过
    # filter: pymunk.ShapeFilter = field(default_factory=pymunk.ShapeFilter)

    # --- 4. 特殊功能 ---
    # sensor: 如果为 True，只触发碰撞回调，不产生物理碰撞效果（即“穿透”但能感知）
    is_sensor: bool = False
    # surface_velocity: 表面速度，可用于制作传送带效果
    surface_velocity: Tuple[float, float] = (0.0, 0.0)