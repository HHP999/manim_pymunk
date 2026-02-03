from manim import *
from manim_pymunk import *


class ConstraintsTest(SpaceScene):
    def construct(self):
        # 1. 两个固定参考点
        center_dot = Dot(UP * 2 + RIGHT * 2)
        fixed_dot = Dot(UP * 0.5 + LEFT * 2, color=RED)
        # 2. 轮子 (Wheel) - 动态
        wheel = Circle(radius=0.6, fill_opacity=1, fill_color=RED).move_to(center_dot)
        groove_line = Line(fixed_dot.get_center(), RIGHT * 5 )
        rod = Line(wheel.get_top(), groove_line.get_end(), color=YELLOW)

        self.add_dynamic_body(wheel, groove_line, rod)
        self.add_static_body(center_dot, fixed_dot)
        wheel.body.angular_velocity = 6

        # 钉住轮子中心并给动力
        wheel_pivot = VPivotJoint(center_dot, wheel, pivot=center_dot.get_center())
        # 关键修改：用 PivotJoint 把滑轨的左端钉在固定点上
        groove_hinge = VPivotJoint(fixed_dot, groove_line, pivot=fixed_dot.get_center())
        # 5. 建立连接关节
        # 关节 A: 连杆一端钉在轮子边缘
        vPivot_rod_wheel = VPivotJoint(wheel, rod, pivot=wheel.get_top())
        # 关节 B: 连杆另一端在“会摆动的滑轨”上滑动
        # 注意：groove_a/b 是相对于 groove_line 质心的局部坐标
        vGroove = VGrooveJoint(
            groove_line,
            rod,
            groove_a=groove_line.get_start() - groove_line.get_center(),
            groove_b=groove_line.get_end() - groove_line.get_center(),
            anchor_b=rod.get_end() - rod.get_center(),
        )
        # 6. 过滤碰撞，防止组件互相弹飞
        self.add_shape_filter(center_dot, wheel, rod, groove_line, group=3)
        # 添加所有约束
        self.add_constraints_body(wheel_pivot, groove_hinge, vPivot_rod_wheel, vGroove)

        self.wait(6)
        # self.draw_debug_img()
