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
        role_dot2 = Dot(center_dot.get_center(), radius=1)
        role_dot2.add(
            Line(start=role_dot2.get_center(), end=role_dot2.get_top(), color=RED)
        )

        self.add_static_body(center_dot)
        self.add_dynamic_body(role_dot2, role_dot)

        role_dot.body.angular_velocity = 6
        role_dot2.body.angular_velocity = -6
        self.add_shape_filter(center_dot, role_dot, role_dot2, group=3)

        role_pin = VPivotJoint(center_dot, role_dot, pivot=center_dot.get_center())

        role_pin2 = VPivotJoint(center_dot, role_dot2, pivot=center_dot.get_center())

        vRotaryLimitJoint = VRotaryLimitJoint(
            role_dot2,
            role_dot,
            min_angle=-90 * DEGREES,
            max_angle=90 * DEGREES,
    
        )

        # 2. 添加约束
        self.add_constraints_body(role_pin, role_pin2, vRotaryLimitJoint)

        self.wait(6)
        # self.draw_debug_img()
