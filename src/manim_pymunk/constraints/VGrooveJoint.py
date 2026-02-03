from typing import Optional
from pymunk.constraints import GrooveJoint
 
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk import Space


# a 上的滑轨，b 在滑轨运动
class VGrooveJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        groove_a: np.ndarray = LEFT,
        groove_b: np.ndarray = RIGHT,
        anchor_b: np.ndarray = ORIGIN,

        groove_color: ManimColor = GREEN,
        pivot_appearance: Mobject = Dot(color=YELLOW),
        show_groove: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Pymunk local coordinates (x, y)
        self.groove_a_local = tuple(groove_a[:2])
        self.groove_b_local = tuple(groove_b[:2])
        self.anchor_b_local = tuple(anchor_b[:2])

        self.pivot_appearance = pivot_appearance
        self.show_groove = show_groove
        self.groove_line = None
        self.constraint: Optional[GrooveJoint] = None
        self.groove_color = groove_color

    def install(self, space: Space):
        """Install physics constraint and initialize track/pivot visuals."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VGrooveJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk GrooveJoint
        self.constraint = GrooveJoint(
            a_body,
            b_body,
            self.groove_a_local,
            self.groove_b_local,
            self.anchor_b_local,
        )

        # 2. Sync initial visual position
        # Calculate world coordinates for the groove start, end, and the pivot
        ga_world = a_body.local_to_world(self.groove_a_local)
        gb_world = a_body.local_to_world(self.groove_b_local)
        p_world = b_body.local_to_world(self.anchor_b_local)

        p1 = [ga_world.x, ga_world.y, 0]
        p2 = [gb_world.x, gb_world.y, 0]
        pp = [p_world.x, p_world.y, 0]

        # Initialize the groove line (the track)
        if self.show_groove:
            self.groove_line = Line(p1, p2, color=self.groove_color, stroke_width=2)
        else:
            self.groove_line = VMobject()

        self.pivot_appearance.move_to(pp)

        # Add to VConstraint
        self.add(self.groove_line, self.pivot_appearance)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Sync the visual track and pivot with the physics bodies."""
        if not self.constraint:
            return

        # Body A defines the groove track
        wa_start = self.constraint.a.local_to_world(self.constraint.groove_a)
        wa_end = self.constraint.a.local_to_world(self.constraint.groove_b)

        # Body B defines the pivot point
        wb_pivot = self.constraint.b.local_to_world(self.constraint.anchor_b)

        p1 = [wa_start.x, wa_start.y, 0]
        p2 = [wa_end.x, wa_end.y, 0]
        pp = [wb_pivot.x, wb_pivot.y, 0]

        # Update the pivot point position
        self.pivot_appearance.move_to(pp)

        # Update the groove line (it moves and rotates with Body A)
        if self.show_groove and isinstance(self.groove_line, Line):
            self.groove_line.put_start_and_end_on(p1, p2)
