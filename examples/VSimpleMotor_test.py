from manim import *
from manim_pymunk import *


class ConstraintsTest(SpaceScene):
    def construct(self):
        # 1. 两个固定参考点
        center_dot = Dot(ORIGIN)
        role_dot = Dot(center_dot.get_center(), radius=0.5, color=RED)
        role_dot.add(
            Line(start=role_dot.get_center(), end=role_dot.get_top(), color=BLUE)
        )

        self.add_static_body(center_dot)
        self.add_dynamic_body(role_dot)

        self.add_shape_filter(center_dot, role_dot, group=3)

        role_pin = VPivotJoint(center_dot, role_dot, pivot=center_dot.get_center())
        vSimpleMotor = VSimpleMotor(center_dot, role_dot, rate=2)

        # 2. 添加约束
        self.add_constraints_body(vSimpleMotor, role_pin)

        self.wait(9)
        # self.draw_debug_img()
