from tracemalloc import start
from typing import Optional
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import SlideJoint
from pymunk import Space


class VSlideJoint(VConstraint):
    """Initializes a Slide Joint constraint between two Mobjects.

    A Slide Joint holds two bodies between a minimum and maximum distance. 
    It acts like a solid link when the distance reaches the limits, but 
    allows free movement within the specified range.

    Parameters
    ----------
    a_mob
        The first Mobject to connect.
    b_mob
        The second Mobject to connect.
    anchor_a_local
        The anchor point on the first body, defined in local coordinates.
    anchor_b_local
        The anchor point on the second body, defined in local coordinates.
    min_dist
        The minimum allowed distance between the two anchor points.
    max_dist
        The maximum allowed distance between the two anchor points.
    anchor_a_appearance
        The visual representation (Mobject) of the first anchor point.
    anchor_b_appearance
        The visual representation (Mobject) of the second anchor point.
    indicator_line_class
        The Manim class used to draw the connection line (e.g., Line or DashedLine). 
        Pass None to disable the visual indicator.
    indicator_line_config
        Configuration dictionary for the styling of the indicator line.

    Examples
    --------
    .. manim:: VSlideJointExample

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

    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a_local: list[float, float, float] = ORIGIN,
        anchor_b_local: list[float, float, float] = ORIGIN,
        min_dist: float = 0.0,
        max_dist: float = 1.0,
        anchor_a_appearance: Mobject = Dot(color=GREEN_A, radius=0.08),
        anchor_b_appearance: Mobject = Dot(color=GREEN_A, radius=0.08),
        indicator_line_class: Optional[Line] = Line,
        indicator_line_config: dict = {
            "color": RED,
            "stroke_width": 2,
        },
        **kwargs,
    ):

        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        self.anchor_a_local = anchor_a_local
        self.anchor_b_local = anchor_b_local

        self.min_dist = min_dist
        self.max_dist = max_dist

        self.anchor_a_appearance = anchor_a_appearance
        self.anchor_b_appearance = anchor_b_appearance
        self.indicator_line_class = indicator_line_class
        self.indicator_line_config = indicator_line_config
        self.indicator_line = None
        self.constraint: Optional[SlideJoint] = None

    def __check_data(self):
        """Verify the validity of constraint parameters."""
        pass

    def install(self, space: Space):
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VSlideJoint connected objects must have Pymunk bodies.")

        self.constraint = SlideJoint(
            a_body,
            b_body,
            tuple(self.anchor_a_local[:2]),
            tuple(self.anchor_b_local[:2]),
            self.min_dist,
            self.max_dist,
        )

        pos_a = a_body.local_to_world(tuple(self.anchor_a_local[:2]))
        pos_b = b_body.local_to_world(tuple(self.anchor_b_local[:2]))
        p1 = [pos_a.x, pos_a.y, 0]
        p2 = [pos_b.x, pos_b.y, 0]

        if self.indicator_line_class:
            self.indicator_line = self.indicator_line_class(
                start=p1, end=p2, **self.indicator_line_config
            )
            self.add(self.indicator_line)

        self.anchor_a_appearance.move_to(p1)
        self.anchor_b_appearance.move_to(p2)

        self.add(self.anchor_a_appearance, self.anchor_b_appearance)

        space.add(self.constraint)
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Visual control updater"""
        if not self.constraint:
            return

        a_body = self.constraint.a
        b_body = self.constraint.b
        wa = a_body.local_to_world(self.constraint.anchor_a)
        wb = b_body.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.anchor_a_appearance.move_to(p1)
        self.anchor_b_appearance.move_to(p2)

        if isinstance(self.indicator_line, Line):
            self.indicator_line.put_start_and_end_on(p1, p2)
