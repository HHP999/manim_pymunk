from manim import *
from manim_pymunk import *


class ConstraintsTest(SpaceScene):
    def construct(self):
        # 1. 配置静态地面
        ground = Line(LEFT * 5 + DOWN * 2, RIGHT * 5 + DOWN * 3)
        self.add_static_body(ground)

        static_anchor = Dot(UP * 3 + LEFT * 3, color=YELLOW)

        static_anchor_square = Square(side_length=1).shift(UP)
        dot1 = Dot(static_anchor_square.get_corner(DR), radius=0.3, color=YELLOW)
        dot1.add(Line(dot1.get_center(), dot1.get_top(), color=BLUE, stroke_width=10))

        dot2 =Gear(radius=0.5).set_color(RED).move_to(static_anchor_square.get_corner(UL))

        self.add_static_body(static_anchor)
        self.add_dynamic_body(static_anchor_square, dot1, dot2)

        vPinJoint_static_anchor_square = VPinJoint(
            static_anchor,
            static_anchor_square,
            connect_line_class=Line,
            connect_line_style={"stroke_width": 2, "color": WHITE},
        )

        vPivotJoint = VPivotJoint(static_anchor_square, dot1, pivot=dot1.get_center())
        vPivotJoint2 = VPivotJoint(
            static_anchor_square,
            dot2,
            anchor_a=static_anchor_square.get_corner(UL)
            - static_anchor_square.get_center(),
            anchor_b=ORIGIN,
        )

        self.add_shape_filter(dot1, dot2, static_anchor_square, group=2)

        vGearJoint = VGearJoint(
            dot1,
            dot2,
            phase=PI / 2,
            ratio=10.0,
        )
        dot1.body.angular_velocity = 2 * PI  # 弧度/秒
        self.add_constraints_body(
            vPivotJoint, vPivotJoint2, vPinJoint_static_anchor_square, vGearJoint
        )
        self.draw_debug_img()
