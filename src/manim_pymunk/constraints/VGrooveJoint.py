from typing import Optional
from pymunk.constraints import GrooveJoint

from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk import Space


class VGrooveJoint(VConstraint):
    """Initializes a Groove Joint constraint between two Mobjects.

    A Groove Joint constrains a point on the second body to a line segment 
    (the "groove") on the first body. The groove is defined by two points 
    relative to the first body's center, and the anchor point is relative 
    to the second body's center.

    Parameters
    ----------
    a_mob
        The Mobject that contains the groove (the rail/track).
    b_mob
        The Mobject that contains the sliding anchor (the slider).
    groove_a_local
        The start point of the groove, in `a_mob`'s local coordinates.
    groove_b_local
        The end point of the groove, in `a_mob`'s local coordinates.
    anchor_b_local
        The anchor point on `b_mob` that slides within the groove, in local coordinates.
    groove_a_appearance
        Visual Mobject representing the start of the groove.
    groove_b_appearance
        Visual Mobject representing the end of the groove.
    anchor_b_appearance
        Visual Mobject representing the sliding anchor on the second body.
    groove_line_class
        The Manim class used to draw the groove line (e.g., Line or DashedLine).
    groove_line_config
        Configuration dictionary for the styling of the groove line.

    Examples
    --------
    .. manim:: VGrooveJointExample

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

    """ 

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        groove_a_local: list[float, float, float] = RIGHT,
        groove_b_local: list[float, float, float] = RIGHT * 2,
        anchor_b_local: list[float, float, float] = ORIGIN,
        groove_a_appearance: Mobject = Dot(color=RED),
        groove_b_appearance: Mobject = Dot(color=RED),
        anchor_b_appearance: Mobject = Dot(color=GREEN),
        groove_line_class: Optional[Line] = Line,
        groove_line_config: dict = {
            "color": YELLOW,
            "stroke_width": 2,
        },
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        self.groove_a_local = groove_a_local
        self.groove_b_local = groove_b_local
        self.anchor_b_local = anchor_b_local

        self.groove_a_appearance = groove_a_appearance
        self.groove_b_appearance = groove_b_appearance
        self.anchor_b_appearance = anchor_b_appearance
        self.groove_line_class = groove_line_class
        self.groove_line_config = groove_line_config
        self.groove_line = None

        self.constraint: Optional[GrooveJoint] = None

    def install(self, space: Space):
        """Verify the validity of constraint parameters."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VGrooveJoint connected objects must have Pymunk bodies.")

        self.constraint = GrooveJoint(
            a_body,
            b_body,
            tuple(self.groove_a_local[:2]),
            tuple(self.groove_b_local[:2]),
            tuple(self.anchor_b_local[:2]),
        )

        groove_a_world = a_body.local_to_world(tuple(self.groove_a_local[:2]))
        groove_b_world = a_body.local_to_world(tuple(self.groove_b_local[:2]))
        anchor_b_world = b_body.local_to_world(tuple(self.anchor_b_local[:2]))

        ga = [groove_a_world.x, groove_a_world.y, 0]
        gb = [groove_b_world.x, groove_b_world.y, 0]
        ab = [anchor_b_world.x, anchor_b_world.y, 0]

        if self.groove_line_class:
            self.groove_line = self.groove_line_class(ga, gb, **self.groove_line_config)
            self.add(self.groove_line)

        self.groove_a_appearance.move_to(ga)
        self.groove_b_appearance.move_to(gb)
        self.anchor_b_appearance.move_to(ab)

        self.add(
            self.groove_a_appearance, self.groove_b_appearance, self.anchor_b_appearance
        )

        space.add(self.constraint)
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Visual control updater"""
        if not self.constraint:
            return

        a_body = self.constraint.a
        b_body = self.constraint.b
        # 2. Sync initial visual position
        groove_a_world = a_body.local_to_world(tuple(self.groove_a_local[:2]))
        groove_b_world = a_body.local_to_world(tuple(self.groove_b_local[:2]))
        anchor_b_world = b_body.local_to_world(tuple(self.anchor_b_local[:2]))

        ga = [groove_a_world.x, groove_a_world.y, 0]
        gb = [groove_b_world.x, groove_b_world.y, 0]
        ab = [anchor_b_world.x, anchor_b_world.y, 0]

        self.groove_a_appearance.move_to(ga)
        self.groove_b_appearance.move_to(gb)
        self.anchor_b_appearance.move_to(ab)

        if isinstance(self.groove_line, Line):
            self.groove_line.put_start_and_end_on(ga, gb)
