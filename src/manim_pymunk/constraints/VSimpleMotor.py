from math import inf
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import SimpleMotor
from pymunk import Space
from typing import Optional


class VSimpleMotor(VConstraint):
    """Initializes a Simple Motor constraint between two Mobjects.

    A Simple Motor maintains a constant relative angular velocity between two
    bodies. It applies the necessary torque to reach and maintain the target
    rotation rate, up to a defined maximum torque limit.

    Parameters
    ----------
    a_mob
        The first Mobject (often the base or stator).
    b_mob
        The second Mobject (often the rotor or driven part).
    rate
        The target relative angular velocity in radians per second.
    max_torque
        The maximum torque the motor can apply to achieve the target rate.
        Setting this to a finite value allows the motor to "stall" under load.
    indicator_line_class
        The Manim class used to visualize the rotation (e.g., Arrow or CurvedArrow).
    indicator_line_config
        Configuration dictionary for the styling of the visual indicator.


    Examples
    --------
    .. manim:: VSimpleMotorExample

        from manim_pymunk import *

        class VSimpleMotorExample(SpaceScene):
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
                    VSimpleMotor(
                        static_dot,
                        square,
                        rate=4,
                        max_torque=500,
                    ),
                ]

                self.add_static_body(static_dot)
                self.add_dynamic_body(square, square2)
                self.add_shapes_filter(static_dot, square, square2, group=2)
                self.add_constraints(*constraints)
                self.wait(3)


    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        rate: float = PI,
        max_torque: float = inf,
        indicator_line_class: Optional[Line] = Arrow,
        indicator_line_config: dict = {
            "color": RED,
            "stroke_width": 2,
        },
        **kwargs,
    ):

        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Motor properties
        self.rate = rate  # Desired relative angular velocity
        self.max_torque = max_torque

        self.indicator_line_class = indicator_line_class
        self.indicator_line_config = indicator_line_config
        self.indicator_line = None
        self.constraint: Optional[SimpleMotor] = None

    def __check_data(self):
        """Verify the validity of constraint parameters."""
        pass

    def install(self, space: Space):
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VSimpleMotor connected objects must have Pymunk bodies.")

        self.constraint = SimpleMotor(a_body, b_body, self.rate)

        self.constraint.max_force = self.max_torque

        if self.indicator_line_class is not None:
            self.indicator_line = Line(
                start=self.b_mob.get_center(),
                end=self.b_mob.get_start(),
                **self.indicator_line_config,
            )
            self.add(self.indicator_line)

        space.add(self.constraint)

        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Visual control updater"""
        if not self.constraint:
            return

        if isinstance(self.indicator_line, Line):
            self.indicator_line.put_start_and_end_on(
                start=self.b_mob.get_center(),
                end=self.b_mob.get_start(),
            )
