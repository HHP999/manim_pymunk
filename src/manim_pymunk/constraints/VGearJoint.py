from typing import Optional
from pymunk import Space
from pymunk.constraints import GearJoint
from manim import *
from manim_pymunk.constraints import VConstraint


class VGearJoint(VConstraint):
    """A gear joint constrains the rotational speeds of two rigid bodies.
    It ensures that the two bodies rotate relative to each other at a fixed ratio,
    simulating the mechanical link of a gear system or a belt drive.

    Parameters
    ----------
    a_mob
        The first Mobject to be connected. Typically represents the driving
        or reference gear.
    b_mob
        The second Mobject to be connected. Its rotation is linked to `a_mob`
        based on the defined `ratio`.
    phase
        The angular offset (in radians) between the two bodies. Adjusts the
        initial relative orientation alignment.
    ratio
        The gear ratio. Defines how the angular velocity of `b_mob` relates to
        `a_mob`. For example, a ratio of 2.0 means `b_mob` rotates twice as
        fast as `a_mob`.
    indicator_line_class
        The class used to visualize the rotational direction or connection
        (defaults to `Arrow`). If set to `None`, no indicator will be rendered.
    indicator_line_config
        A dictionary defining the visual style of the indicator line,
        including `color` and `stroke_width`.

    Examples
    --------
    .. manim:: VGearJointExample

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

    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        phase: float = 0.0,
        ratio: float = 1.0,
        indicator_line_class: Optional[Line] = Arrow,
        indicator_line_config: dict = {
            "color": BLUE,
            "stroke_width": 2,
        },
        indicator_length: float = 0.4,
        **kwargs,
    ):

        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob
        self.phase = phase
        self.ratio = ratio
        self.indicator_a = None
        self.indicator_b = None
        self.constraint: Optional[GearJoint] = None
        self.indicator_line_class = indicator_line_class
        self.indicator_line_config = indicator_line_config
        self.indicator_length = indicator_length

    def install(self, space: Space):
        """Verify the validity of constraint parameters."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VGearJoint connected objects must have a Pymunk body.")

        self.constraint = GearJoint(a_body, b_body, self.phase, self.ratio)

        if self.indicator_line_class:
            self.indicator_a = self.indicator_line_class(
                self.a_mob.get_center(),
                self.a_mob.get_center() + UP * self.indicator_length,
                **self.indicator_line_config,
            )
            self.indicator_b = self.indicator_line_class(
                self.b_mob.get_center(),
                self.b_mob.get_center() + UP * self.indicator_length,
                **self.indicator_line_config,
            )
            self.add(self.indicator_a, self.indicator_b)

        space.add(self.constraint)
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Visual control updater"""
        if not self.constraint:
            return

        a_body = self.constraint.a
        b_body = self.constraint.b

        if isinstance(self.indicator_a, Line):
            end_a = (
                self.a_mob.get_center()
                + np.array([np.cos(a_body.angle), np.sin(a_body.angle), 0])
                * self.indicator_length
            )

            self.indicator_a.put_start_and_end_on(self.a_mob.get_center(), end_a)

        if isinstance(self.indicator_b, Line):
            end_b = (
                self.b_mob.get_center()
                + np.array([np.cos(b_body.angle), np.sin(b_body.angle), 0])
                * self.indicator_length
            )

            self.indicator_b.put_start_and_end_on(self.b_mob.get_center(), end_b)
