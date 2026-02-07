from manim import *
from manim_pymunk import *


class ConstraintsTest(SpaceScene):
    def construct(self):
        # 1. 两个固定参考点
        center_dot = Dot(UP * 2 + RIGHT * 2)
        fixed_dot = Dot(UP * 0.5 + LEFT * 2, color=RED)
        # 2. 轮子 (Wheel) - 动态
        wheel = Circle(radius=0.6, fill_opacity=1, fill_color=RED).move_to(center_dot)
        wheel2 = Circle(radius=0.6, fill_opacity=1, fill_color=BLUE).move_to(fixed_dot)
  

        self.add_dynamic_body(wheel, wheel2)
        self.add_static_body(center_dot, fixed_dot)
        wheel.body.angular_velocity = 6
        wheel_pivot = VPivotJoint(center_dot, wheel, pivot=center_dot.get_center())
        wheel2_pivot = VPivotJoint(fixed_dot, wheel2, pivot=fixed_dot.get_center())
        
        ratchet_joint = VRatchetJoint(wheel, wheel2, phase=0, ratchet=PI / 4)
    
        # 6. 过滤碰撞，防止组件互相弹飞
        self.add_shape_filter(center_dot, fixed_dot, wheel, wheel2, group=3)
        # 添加所有约束
        self.add_constraints_body(wheel_pivot, wheel2_pivot, ratchet_joint)

        self.wait(6)
        # self.draw_debug_img()
