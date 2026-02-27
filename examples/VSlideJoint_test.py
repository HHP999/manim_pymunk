from manim import *
from manim_pymunk import *


class VSlideJointExample(SpaceScene):
    def construct(self):

        static_dot = Dot(ORIGIN)
        square = Square().move_to(static_dot).scale(2)
        square2 = Square().move_to(static_dot.get_center() + UR*3).scale(0.5)

        constraints = [
            VPinJoint(static_dot, square),
            VSlideJoint(
                square,
                square2,
                anchor_a_local=square.get_corner(UR) - square.get_center(),
                min_dist=0.5,
                max_dist=3,
            ),
            VSimpleMotor(
                static_dot,
                square,
                rate=PI/4,
                max_torque=500,
            ),
        ]

        self.add_static_body(static_dot)
        self.add_dynamic_body(square, square2)
        self.add_shapes_filter(static_dot, square, square2, group=2)
        self.add_constraints(*constraints)
        self.wait(6)
