from manim import *
from manim_pymunk import *


class VGrooveJointExample(SpaceScene):
    def construct(self):

        static_dot = Dot()

        square_1 = Square().move_to(static_dot)
        square_2 = Square().move_to(static_dot.get_center() + RIGHT * 4).scale(0.3)

        constraints = [
            VGrooveJoint(
                square_1,
                square_2,
                groove_a_local=RIGHT * 2,
                groove_b_local=RIGHT * 4,
            ),
            VPinJoint(static_dot, square_1),
        ]

        self.add_static_body(static_dot)
        self.add_dynamic_body(square_1, angular_velocity=PI * 2)
        self.add_dynamic_body(square_2)

        self.add_shapes_filter(static_dot, square_1, square_2, group=2)
        self.add_constraints(*constraints)
        self.wait(6)
