from manim import *
from manim_pymunk import *


class VGearJointExample(SpaceScene):
    def construct(self):
        floor = Line(LEFT * 10, RIGHT * 10).shift(DOWN * 2)

        static_dot1 = Dot(UP * 2)
        static_dot2 = Dot(UP * 2 + RIGHT * 4)

        square_1 = Square().move_to(static_dot1)
        square_2 = Square().move_to(static_dot2)

        constraints = [
            VGearJoint(
                square_1,
                square_2,
                phase=0,
                ratio=4,
            ),
            VPinJoint(static_dot1, square_1),
            VPinJoint(static_dot2, square_2),
        ]

        self.add_static_body(floor, static_dot1, static_dot2)
        self.add_dynamic_body(square_1, angular_velocity=PI * 2)
        self.add_dynamic_body(square_2)

        self.add_shapes_filter(static_dot1, static_dot2, square_1, square_2, group=2)
        self.add_constraints(*constraints)
        self.wait(3)
