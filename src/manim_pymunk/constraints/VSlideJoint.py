from typing import Optional
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import SlideJoint
from pymunk import Space

class VSlideJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a: np.ndarray = ORIGIN,
        anchor_b: np.ndarray = ORIGIN,
        min_dist: float = 0.0,
        max_dist: float = 1.0,
        mob_a_appearance: Mobject = Dot(color=GREEN_A, radius=0.08),
        mob_b_appearance: Mobject = Dot(color=GREEN_A, radius=0.08),
        show_line: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Pymunk local coordinates
        self.anchor_a_local = tuple(anchor_a[:2])
        self.anchor_b_local = tuple(anchor_b[:2])

        # Slide limits
        self.min_dist = min_dist
        self.max_dist = max_dist

        self.appearance_a = mob_a_appearance
        self.appearance_b = mob_b_appearance
        self.show_line = show_line
        self.line = None
        self.constraint: Optional[SlideJoint] = None

    def install(self, space: Space):
        """Install physics constraint and initialize visuals."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VSlideJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk SlideJoint
        self.constraint = SlideJoint(
            a_body,
            b_body,
            self.anchor_a_local,
            self.anchor_b_local,
            self.min_dist,
            self.max_dist,
        )

        # 2. Sync initial visual position
        pos_a = a_body.local_to_world(self.anchor_a_local)
        pos_b = b_body.local_to_world(self.anchor_b_local)
        p1 = [pos_a.x, pos_a.y, 0]
        p2 = [pos_b.x, pos_b.y, 0]

        # Initialize the connection line
        if self.show_line:
            # We use a dashed line often for slide joints to distinguish from PinJoints
            self.line = DashedLine(p1, p2, color=GREEN_B, stroke_width=2)
        else:
            self.line = VMobject()

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        self.add(self.line, self.appearance_a, self.appearance_b)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Update the tether line and anchors based on physics bodies."""
        if not self.constraint:
            return

        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        wb = self.constraint.b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        if self.show_line and isinstance(self.line, (Line, DashedLine)):
            self.line.put_start_and_end_on(p1, p2)

            # Visual flair: Change line opacity or color when at the limit
            dist = np.linalg.norm(np.array(p1) - np.array(p2))
            if dist >= self.max_dist * 0.98 or dist <= self.min_dist * 1.02:
                self.line.set_stroke(opacity=1.0, width=3)
            else:
                self.line.set_stroke(opacity=0.4, width=2)
