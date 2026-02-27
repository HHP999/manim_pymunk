from manim import *
from manim_pymunk import *

class VDampedRotarySpringExample(SpaceScene):
    def construct(self):
        floor = Line(LEFT * 10, RIGHT * 10).shift(DOWN*2)

        square_1 = Square().next_to(floor, UP)
        square_2 = Square().move_to(square_1.get_center() + RIGHT * 4)

        constraint = VDampedRotarySpring(
            square_1,
            square_2,
            rest_angle=PI / 4,
            stiffness=100,
            damping=1,
        )

        self.add_static_body(floor)
        self.add_dynamic_body(square_1, square_2)
        self.add_constraints(constraint)

        self.wait(3)
