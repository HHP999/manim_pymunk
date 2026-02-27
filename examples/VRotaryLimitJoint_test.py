from manim import *
from manim_pymunk import *


class VRotaryLimitJointExample(SpaceScene):
    def construct(self):

        static_dot = Dot(ORIGIN)
        square = Square().move_to(static_dot)
        square2 = Square().move_to(static_dot.get_center() + UP * 2).scale(0.5)

        constraints = [
            VPinJoint(static_dot, square),
            VPinJoint(
                square,
                square2,
                anchor_a_local=square.get_corner(UR) - square.get_center(),
                distance=2,
                connect_line_class=Line,
            ),
            VRotaryLimitJoint(
                static_dot,
                square2,
                min_angle=-PI / 6,
                max_angle=PI / 6,
            ),
        ]

        self.add_static_body(static_dot)
        self.add_dynamic_body(square, square2, angular_velocity=PI * 2)
        self.add_shapes_filter(static_dot, square, square2, group=2)
        self.add_constraints(*constraints)
        self.wait(3)
