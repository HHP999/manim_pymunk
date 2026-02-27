from typing import Optional
from manim_pymunk.custom_mobjects import VSpring
from pymunk import Space
from pymunk.constraints import DampedSpring
from manim import *
from manim_pymunk.constraints import VConstraint


class VDampedSpring(VConstraint):
    """A damped spring connection is created between two rigid bodies.
    The spring applies a restorative force proportional to the displacement
    from its rest length, while the damping simulates energy loss to
    suppress oscillations.

    Parameters
    ----------
    a_mob
        The first Mobject to be connected. Acts as one of the anchor points
        for the spring.
    b_mob
        The second Mobject to be connected. Linked to `a_mob` via the
        physical spring constraint.
    anchor_a_local
        The local anchor point on `a_mob` where the spring is attached,
        relative to the Mobject's center.
    anchor_b_local
        The local anchor point on `b_mob` where the spring is attached,
        relative to the Mobject's center.
    rest_length
        The equilibrium length of the spring. When the distance between anchors
        equals this value, the spring exerts no force.
    stiffness
        The spring constant $k$ (Young's modulus). Determines how strongly
        the spring pulls or pushes to return to `rest_length`.
    damping
        The damping coefficient $c$. Used to simulate viscous friction,
        causing the kinetic energy of the system to dissipate over time.
    mob_a_appearance
        The Mobject used to visually represent the anchor point on `a_mob`
        (e.g., a `Dot`).
    mob_b_appearance
        The Mobject used to visually represent the anchor point on `b_mob`
        (e.g., a `Dot`).
    connect_line_class
        The class used to visualize the spring body (defaults to `VSpring`).
        If set to `None`, the spring connection will be invisible.
    connect_line_config
        A dictionary defining the visual style of the `connect_line_class`,
        such as `color` and `stroke_width`.

    Examples
    --------
    .. manim:: VDampedSpringExample

        from manim_pymunk import *

        class VDampedSpringExample(SpaceScene):
            def construct(self):
                floor = Line(LEFT * 10, RIGHT * 10).shift(DOWN*2)

                square_1 = Square().next_to(floor, UP)
                square_2 = Square().move_to(square_1.get_center() + UP * 4)

                constraint = VDampedSpring(
                    square_1,
                    square_2,
                    rest_length=3,
                    stiffness=100,
                    damping=10,
                )

                self.add_static_body(floor)
                self.add_dynamic_body(square_1, square_2)
                self.add_constraints(constraint)

                self.wait(3)

    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a_local: list[float, float, float] = ORIGIN,
        anchor_b_local: list[float, float, float] = ORIGIN,
        rest_length: float = 1.0,
        stiffness: float = 100.0,
        damping: float = 10.0,
        mob_a_appearance: Mobject = Dot(color=BLUE),
        mob_b_appearance: Mobject = Dot(color=BLUE),
        connect_line_class: Optional[Line] = VSpring,
        connect_line_config: dict = {"color": YELLOW, "stroke_width": 2},
        **kwargs,
    ):

        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob
        self.anchor_a_local = anchor_a_local
        self.anchor_b_local = anchor_b_local

        # Spring physics properties
        self.rest_length = rest_length
        self.stiffness = stiffness
        self.damping = damping

        self.appearance_a = mob_a_appearance
        self.appearance_b = mob_b_appearance
        self.connect_line_class = connect_line_class
        self.connect_line_config = connect_line_config
        self.conn_line: Optional[VMobject] = None
        self.constraint: Optional[DampedSpring] = None

    def install(self, space: Space):
        """Verify the validity of constraint parameters."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VDampedSpring connected objects must have a Pymunk body.")

        self.constraint = DampedSpring(
            a_body,
            b_body,
            tuple(self.anchor_a_local[:2]),
            tuple(self.anchor_b_local[:2]),
            self.rest_length,
            self.stiffness,
            self.damping,
        )

        pos_a = a_body.local_to_world(tuple(self.anchor_a_local[:2]))
        pos_b = b_body.local_to_world(tuple(self.anchor_b_local[:2]))
        p1 = [pos_a.x, pos_a.y, 0]
        p2 = [pos_b.x, pos_b.y, 0]

        if self.connect_line_class:
            self.conn_line = self.connect_line_class(p1, p2, **self.connect_line_config)

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        self.add(self.conn_line, self.appearance_a, self.appearance_b)

        space.add(self.constraint)
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Visual control updater"""
        if not self.constraint:
            return

        body_a = self.constraint.a
        body_b = self.constraint.b
        wa = body_a.local_to_world(self.constraint.anchor_a)
        wb = body_b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        if self.conn_line:
            self.conn_line.put_start_and_end_on(p1, p2)
