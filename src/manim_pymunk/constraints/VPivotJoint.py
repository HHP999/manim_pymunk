from tkinter.messagebox import NO
from typing import Optional
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import PivotJoint
from pymunk import Space


class VPivotJoint(VConstraint):
    """A pivot joint allows two rigid bodies to rotate freely around a common
    pivot point. The pivot point acts as an axis of rotation, ensuring that
    both bodies remain attached at the specified position regardless of
    external forces.

    Please configure pivot_world or (anchor_a_loca, anchor_b_local).

    Parameters
    ----------
    a_mob
        The first Mobject to be connected.
    b_mob
        The second Mobject to be connected.
    pivot_world
        The global coordinate position of the pivot point. If provided,
        `anchor_a_local` and `anchor_b_local` are calculated automatically based on this.
    anchor_a_local
        The local anchor point on `a_mob` corresponding to the pivot,
        relative to the Mobject's center.
    anchor_b_local
        The local anchor point on `b_mob` corresponding to the pivot,
        relative to the Mobject's center.
    pivot_appearance
        The Mobject used to visually represent the pivot point
        (defaults to a white `Dot` with 0.05 radius).

    Examples
    --------
    .. manim:: VPivotJointExample

        from manim_pymunk import *

        class VPivotJointExample(SpaceScene):
            def construct(self):

                static_dot = Dot(ORIGIN)
                square = Square().move_to(static_dot)
                square2 = Square().move_to(static_dot.get_center() + UP * 2).scale(0.5)

                constraints = [
                    VPivotJoint(static_dot, square),
                    VPivotJoint(
                        square,
                        square2,
                        pivot_world= UP*3,
                    ),
                ]

                self.add_static_body(static_dot)
                self.add_dynamic_body(square, square2, angular_velocity=PI * 2)
                self.add_shapes_filter(static_dot, square, square2, group=2)
                self.add_constraints(*constraints)
                self.wait(3)

    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        pivot_world: list[float, float, float] = None,
        anchor_a_local: list[float, float, float] = ORIGIN,
        anchor_b_local: list[float, float, float] = ORIGIN,
        anchor_a_appearance: Mobject = Dot(color=RED),
        anchor_b_appearance: Mobject = Dot(color=RED),
        pivot_appearance: Mobject = Dot(color=RED),
        connect_line_class: Optional[Line] = Line,
        connect_line_config: dict = {
            "color": YELLOW,
            "stroke_width": 2,
        },
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        self.pivot_world = pivot_world
        self.anchor_a_local = anchor_a_local
        self.anchor_b_local = anchor_b_local

        self.anchor_a_appearance = anchor_a_appearance
        self.anchor_b_appearance = anchor_b_appearance
        self.pivot_appearance = pivot_appearance

        self.connect_line_class = connect_line_class
        self.connect_line_config = connect_line_config
        self.anchor_connect_line = None

        self.pivot_connect_line_a = None
        self.pivot_connect_line_b = None

        self.constraint: Optional[PivotJoint] = None

    def install(self, space: Space):
        """Verify the validity of constraint parameters."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VPivotJoint connected objects must have Pymunk bodies.")

        if self.pivot_world is not None:
            self.constraint = PivotJoint(a_body, b_body, tuple(self.pivot_world[:2]))
            self.pivot_appearance.move_to(self.pivot_world)
            self.add(self.pivot_appearance)
            if self.connect_line_class:
                self.pivot_connect_line_a = self.connect_line_class(
                    self.a_mob.get_center(),
                    self.pivot_world,
                    **self.connect_line_config,
                )

                self.pivot_connect_line_b = self.connect_line_class(
                    self.b_mob.get_center(),
                    self.pivot_world,
                    **self.connect_line_config,
                )
                self.add(self.pivot_connect_line_a, self.pivot_connect_line_b)

        elif self.anchor_a_local is not None and self.anchor_b_local is not None:
            self.constraint = PivotJoint(
                a_body,
                b_body,
                tuple(self.anchor_a_local[:2]),
                tuple(self.anchor_b_local[:2]),
            )
            pos_a = a_body.local_to_world(tuple(self.anchor_a_local[:2]))
            pos_b = b_body.local_to_world(tuple(self.anchor_b_local[:2]))
            p1 = [pos_a.x, pos_a.y, 0]
            p2 = [pos_b.x, pos_b.y, 0]

            if self.connect_line_class:
                self.anchor_connect_line = self.connect_line_class(
                    p1, p2, **self.connect_line_config
                )
                self.add(self.anchor_connect_line)

            self.anchor_a_appearance.move_to(p1)
            self.anchor_b_appearance.move_to(p2)

            self.add(self.anchor_a_appearance, self.anchor_b_appearance)

        else:
            raise "You seem to have forgotten to configure the parameters: pivot_world or (anchor_a_loca, anchor_b_local)!!!"

        space.add(self.constraint)
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Visual control updater"""
        if not self.constraint:
            return

        if self.pivot_world is not None:
            p = self.constraint.anchor_a
            pivot = [p.x, p.y, 0]
            self.pivot_appearance.move_to(pivot)
            if isinstance(self.pivot_connect_line_a, Line):
                self.pivot_connect_line_a.put_start_and_end_on(
                    self.a_mob.get_center(),
                    pivot,
                )
            if isinstance(self.pivot_connect_line_a, Line):
                self.pivot_connect_line_b.put_start_and_end_on(
                    self.b_mob.get_center(),
                    pivot,
                )

        elif self.anchor_a_local is not None and self.anchor_b_local is not None:
            a_body = self.constraint.a
            b_body = self.constraint.b
            wa = a_body.local_to_world(self.constraint.anchor_a)
            wb = b_body.local_to_world(self.constraint.anchor_b)
            p1 = [wa.x, wa.y, 0]
            p2 = [wb.x, wb.y, 0]

            self.anchor_a_appearance.move_to(p1)
            self.anchor_b_appearance.move_to(p2)

            if isinstance(self.anchor_connect_line, Line):
                self.anchor_connect_line.put_start_and_end_on(p1, p2)
