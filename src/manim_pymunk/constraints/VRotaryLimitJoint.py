"""旋转角度限制约束模块。

该模块实现VRotaryLimitJoint类，用于限制两个刚体之间的相对旋转角度，
确保相对旋转角保持在指定的最小和最大值之间。
"""

from manim import *
from typing import Optional
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import RotaryLimitJoint
from pymunk import Space
import numpy as np


class VRotaryLimitJoint(VConstraint):
    """两个刚体之间的旋转角度限制约束。
    
    VRotaryLimitJoint限制两个刚体之间的相对旋转角在[min_angle, max_angle]范围内。
    两个弧形指示器直观地显示当前相对角度和角度限制。
    
    Attributes:
        a_mob (Mobject): 第一个连接的Mobject对象。
        b_mob (Mobject): 第二个连接的Mobject对象。
        min_angle (float): 相对旋转角的最小值（弧度）。
        max_angle (float): 相对旋转角的最大值（弧度）。
        constraint (pymunk.RotaryLimitJoint): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        min_angle: float = -PI / 4,
        max_angle: float = PI / 4,
        arc_indicator_class: Optional[type] = Arc,
        arc_indicator_style: dict = {"radius": 0.5, "color": YELLOW, "stroke_width": 2},
        **kwargs,
    ):
        """初始化旋转角度限制约束。
        
        Args:
            a_mob (Mobject): 第一个连接的Mobject对象。
            b_mob (Mobject): 第二个连接的Mobject对象。
            min_angle (float, optional): 最小相对角度，默认为-π/4。
            max_angle (float, optional): 最大相对角度，默认为π/4。
            arc_indicator_class (Optional[type], optional): 弧形指示器的类型，默认为Arc。
            arc_indicator_style (dict, optional): 弧形指示器的样式配置。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # 物理限制参数
        self.min_angle = min_angle
        self.max_angle = max_angle

        # 视觉样式配置
        self.arc_indicator_class = arc_indicator_class
        self.arc_indicator_style = arc_indicator_style

        # 视觉组件与物理约束占位
        self.arc_a: Optional[VMobject] = None
        self.arc_b: Optional[VMobject] = None
        self.constraint: Optional[RotaryLimitJoint] = None

    def install(self, space: Space):
        """安装旋转限制约束并初始化弧形指示器。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError(
                "VRotaryLimitJoint 连接的物体必须先执行 add_dynamic_body"
            )

        # 1. 创建 Pymunk 物理约束
        self.constraint = RotaryLimitJoint(
            a_body, b_body, self.min_angle, self.max_angle
        )

        # 初始化两个弧形指示器
        if self.arc_indicator_class:
            # 初始状态设为极小角度，避免渲染错误
            self.arc_a = self.arc_indicator_class(
                angle=0, **self.arc_indicator_style
            )
            self.arc_b = self.arc_indicator_class(
                angle=0, **self.arc_indicator_style
            )
            self.add(self.arc_a, self.arc_b)

        # 3. 注入物理世界
        space.add(self.constraint)

        # 4. 绑定实时更新器
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """同步物理状态与弧形指示器的视觉表现。
        
        根据两个刚体的实时位置和旋转角度，更新弧形指示器的位置和朝向。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
        if not self.constraint:
            return

        # 1. 获取物理状态
        body_a = self.constraint.a
        body_b = self.constraint.b

        # 2. 获取 Manim 坐标
        pos_a = np.array([body_a.position.x, body_a.position.y, 0])
        pos_b = np.array([body_b.position.x, body_b.position.y, 0])

        # 3. 计算连线几何信息
        diff = pos_b - pos_a
        dist = np.linalg.norm(diff)

        # 防止重合导致的计算除零错误
        if dist < 0.001:
            unit_vec = np.array([1, 0, 0])
        else:
            unit_vec = diff / dist

        # 4. 计算角度差
        rel_angle = body_b.angle - body_a.angle
        display_angle = rel_angle if abs(rel_angle) > 0.005 else 0.005

        # 5. 更新弧形指示器
        buff = 0.3
        line_angle = np.arctan2(unit_vec[1], unit_vec[0])  # 连线的绝对角度

        if self.arc_a:
            new_arc_a = self.arc_indicator_class(
                angle=display_angle, **self.arc_indicator_style
            )
            target_pos_a = pos_a - unit_vec * (self.a_mob.get_width() / 2 + buff)
            new_arc_a.move_to(target_pos_a)

            # 微调旋转：连线角度 - 弧度的一半，使弧线中点落在直线上
            new_arc_a.rotate(
                line_angle - display_angle / 2 + PI, about_point=target_pos_a
            )
            self.arc_a.become(new_arc_a)

        if self.arc_b:
            # 为了对称，b 处的弧度使用相反方向
            new_arc_b = self.arc_indicator_class(
                angle=-display_angle, **self.arc_indicator_style
            )
            target_pos_b = pos_b + unit_vec * (self.b_mob.get_width() / 2 + buff)
            new_arc_b.move_to(target_pos_b)

            # 微调旋转：连线角度 - 弧度的一半 (注意此时 display_angle 是负的，依然适用)
            new_arc_b.rotate(
                line_angle - (-display_angle) / 2, about_point=target_pos_b
            )
            self.arc_b.become(new_arc_b)

