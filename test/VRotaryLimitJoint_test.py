from random import choice, randint, random
from manim import *
from manim_pymunk import *


color_values = [getattr(AS2700, item) for item in dir(AS2700) if item.isupper()]



class ConstraintsTest(SpaceScene):
    def construct(self):
        nums = 3
        dots_group = VGroup()
        for i in range(nums):
            dot = Dot(radius=0.2, color=choice(color_values))
            anchors = dot.get_anchors()
            dot.add(Line(dot.get_center(), anchors[-1], color=BLUE))
            dots_group.add(dot)
        dots_group.arrange_in_grid(rows=4, buff=0.5).shift(UP * 2)
        square = Square(side_length=0.4, fill_color=YELLOW, fill_opacity=1)
        self.add_dynamic_body(*dots_group, square)
        self.add_static_body(Line(LEFT * 10 + DOWN * 1, RIGHT * 10 + DOWN * 3))

        static_dot = Dot(UP * 3 + LEFT * 3, color=YELLOW)
        self.add_static_body(static_dot)

        v_pinJoint = VPinJoint(static_dot, dots_group[0], show_line=True)
        self.add_constraints_body(v_pinJoint)

        # vDampedRotarySpring = VDampedRotarySpring(
        #     dots_group[0],
        #     square,
        #     rest_angle=0,  #
        #     stiffness=1000.0,
        #     damping=1.0,
        #     show_indicator=True,
        # )
        # self.add_constraints_body(vDampedRotarySpring)

        # vDampedSpring = VDampedSpring(
        #     dots_group[0],
        #     square,
        #     rest_length=0.5,
        #     stiffness=10.0,
        #     damping=1,
        # )
        # self.add_constraints_body(vDampedSpring)

        # vGearJoint = VGearJoint(
        #     dots_group[0],
        #     square,
        #     phase=2,
        #     ratio=1.0,
        #     show_indicator=True,
        # )
        # self.add_constraints_body(vGearJoint)

        # vGrooveJoint = VGrooveJoint(
        #     dots_group[0],
        #     square,
        #     groove_a=LEFT,
        #     groove_b=RIGHT,
        #     anchor_b=ORIGIN,
        #     groove_color=WHITE,
        # )
        # self.add_constraints_body(vGrooveJoint)

        # vPivotJoint = VPivotJoint(
        #     static_dot,
        #     square,
        #     # anchor_a=None,
        #     # anchor_b=None,
        #     # pivot=None,
        # )
        # self.add_constraints_body(vPivotJoint)

        # vRatchetJoint = VRatchetJoint(
        #     static_dot,
        #     square,
        #     phase=PI,
        #     ratchet=PI / 4,
        #     show_connection=True,
        # )
        # self.add_constraints_body(vRatchetJoint)

        # vRotaryLimitJoint = VRotaryLimitJoint(
        #     dots_group[0],
        #     square,
        #     min_angle=-PI / 4,
        #     max_angle=PI / 4,
        #     show_arc=True,
        # )
        # self.add_constraints_body(vRotaryLimitJoint)

        # vSimpleMotor = VSimpleMotor(
        #     static_dot,
        #     square,
        #     rate=-5.0,
        #     max_torque=100.0,
        #     show_direction=True,
        # )
        # self.add_constraints_body(vSimpleMotor)

        vSlideJoint = VSlideJoint(
            dots_group[0],
            square,
            min_dist=0,
            max_dist=2,
        )
        self.add_constraints_body(vSlideJoint)

        self.wait(5)
