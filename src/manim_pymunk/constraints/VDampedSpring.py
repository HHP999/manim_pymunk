

from typing import Optional
from manim_pymunk.custom_mobjects import VSpring
from pymunk import Space
from pymunk.constraints import DampedSpring
from manim import *
from manim_pymunk.constraints import VConstraint
# 已测试
class VDampedSpring(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a: np.ndarray = ORIGIN,
        anchor_b: np.ndarray = ORIGIN,
        rest_length: float = 1.0,
        stiffness: float = 100.0,
        damping: float = 10.0,
        mob_a_appearance: Mobject = Dot(color=BLUE),
        mob_b_appearance: Mobject = Dot(color=BLUE),
        connect_line_class: Optional[Line] = VSpring,
        connect_line_style: dict = {"color": YELLOW, "stroke_width": 2},
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Pymunk compatibility: store as (x, y) tuples
        self.anchor_a_local = tuple(anchor_a[:2])
        self.anchor_b_local = tuple(anchor_b[:2])

        # Spring physics properties
        self.rest_length = rest_length
        self.stiffness = stiffness
        self.damping = damping

        self.appearance_a = mob_a_appearance
        self.appearance_b = mob_b_appearance
        self.connect_line_class = connect_line_class
        self.connect_line_style = connect_line_style
        self.conn_line: Optional[VMobject] = None
        self.constraint: Optional[DampedSpring] = None

    def install(self, space: Space):
        """Install physics constraint and initialize visual mobjects."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VDampedSpring connected objects must have a Pymunk body.")

        # 1. Create Pymunk DampedSpring
        self.constraint = DampedSpring(
            a_body,
            b_body,
            self.anchor_a_local,
            self.anchor_b_local,
            self.rest_length,
            self.stiffness,
            self.damping,
        )

        # 2. Sync initial visual position
        pos_a = a_body.local_to_world(self.anchor_a_local)
        pos_b = b_body.local_to_world(self.anchor_b_local)
        p1 = [pos_a.x, pos_a.y, 0]
        p2 = [pos_b.x, pos_b.y, 0]

        # Initialize visual representation (Simple line or custom Spring)
        if self.connect_line_class:
            # You can replace Line with a custom zig-zag VMobject for a "spring" look
            self.conn_line = self.connect_line_class(p1, p2, **self.connect_line_style)

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        self.add(self.conn_line, self.appearance_a, self.appearance_b)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Sync visual state with physics engine every frame."""
        if not self.constraint:
            return

        # Get world coordinates from Pymunk
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        wb = self.constraint.b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        if self.conn_line:
            self.conn_line.put_start_and_end_on(p1, p2)
