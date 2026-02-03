from typing import Optional
from pymunk import Space
from pymunk.constraints import GearJoint
from manim import *
from manim_pymunk.constraints import VConstraint

# 已测试
class VGearJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        phase: float = 0.0,
        ratio: float = 1.0,
        indicator_line_class: Optional[Line] = Arrow,  # 锚点样式
        indicator_line_style: dict = {
            "color": BLUE,
            "stroke_width": 2,
        },
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Gear specific properties
        self.phase = phase
        self.ratio = ratio
        self.indicator_a = None
        self.indicator_b = None
        self.constraint: Optional[GearJoint] = None
        self.indicator_line_class = indicator_line_class
        self.indicator_line_style = indicator_line_style

    def install(self, space: Space):
        """Install the angular gear constraint into the physics space."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VGearJoint connected objects must have a Pymunk body.")

        # 1. Create Pymunk GearJoint
        # Enforces: (angle_b - phase) = ratio * angle_a
        self.constraint = GearJoint(a_body, b_body, self.phase, self.ratio)

        # 2. Initialize Visuals
        # Since GearJoints are abstract angular links, we often don't draw a line.
        # However, we can add a visual indicator (like a dashed connection) if desired.
        if self.indicator_line_class:
            self.indicator_a = self.indicator_line_class(
                self.a_mob.get_center(),
                self.a_mob.get_center() + UP * 0.4,
                **self.indicator_line_style,
            )
            self.indicator_b = self.indicator_line_class(
                self.b_mob.get_center(),
                self.b_mob.get_center() + UP * 0.4,
                **self.indicator_line_style,
            )
            self.add(self.indicator_a, self.indicator_b)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """更新视觉指示器（指针），使其跟随刚体的位置和旋转。"""
        if not self.constraint:
            return

        a_body = self.constraint.a
        b_body = self.constraint.b

        # 指针的长度
        length = 0.4

        if self.indicator_a:
            # 计算 a_body 旋转后的末端坐标
            # a_body.angle 是弧度，我们需要计算其在世界空间的方向
            end_a = (
                self.a_mob.get_center()
                + np.array([np.cos(a_body.angle), np.sin(a_body.angle), 0]) * length
            )

            self.indicator_a.put_start_and_end_on(self.a_mob.get_center(), end_a)

        if self.indicator_b:
            # 同理计算 b_body 的末端坐标
            end_b = (
                self.b_mob.get_center()
                + np.array([np.cos(b_body.angle), np.sin(b_body.angle), 0]) * length
            )

            self.indicator_b.put_start_and_end_on(self.b_mob.get_center(), end_b)
