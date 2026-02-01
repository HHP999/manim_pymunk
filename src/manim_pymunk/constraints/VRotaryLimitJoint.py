
from manim import *
from typing import Optional
from manim_pymunk.constraints import VConstraint
from pymunk.constraints  import RotaryLimitJoint
from pymunk import Space
class VRotaryLimitJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        min_angle: float = -PI / 4,
        max_angle: float = PI / 4,
        show_arc: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Angular limits in radians
        self.min_angle = min_angle
        self.max_angle = max_angle

        self.show_arc = show_arc
        self.arc_indicator = None
        self.constraint: Optional[RotaryLimitJoint] = None

    def install(self, space: Space):
        """Install the rotary limit constraint and initialize visual feedback."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError(
                "VRotaryLimitJoint connected objects must have Pymunk bodies."
            )

        # 1. Create Pymunk RotaryLimitJoint
        self.constraint = RotaryLimitJoint(
            a_body, b_body, self.min_angle, self.max_angle
        )

        # 2. Initialize Visuals
        # We visualize the allowed range as an Arc centered on Body A
        if self.show_arc:
            self.arc_indicator = Arc(
                radius=0.5,
                start_angle=self.min_angle,
                angle=self.max_angle - self.min_angle,
                color=YELLOW,
                stroke_width=2,
            ).set_opacity(0.3)
            self.add(self.arc_indicator)
        else:
            self.arc_indicator = VMobject()

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Sync the visual arc with the base body's orientation."""
        if not self.constraint:
            return

        # The limit is relative to Body A's current orientation
        # We move the arc to Body A's center and rotate it to match
        base_pos = self.a_mob.get_center()
        base_angle = self.constraint.a.angle

        self.arc_indicator.move_to(base_pos)
        # Note: Manim uses absolute rotation for set_angle/rotate
        # We align the arc's 'zero' with Body A's orientation
        self.arc_indicator.set_angle(base_angle + self.min_angle)

    def set_limits(self, min_angle: float, max_angle: float):
        """Dynamically update the angular limits."""
        if self.constraint:
            self.constraint.min = min_angle
            self.constraint.max = max_angle
            self.min_angle = min_angle
            self.max_angle = max_angle
            # If visual arc exists, we would ideally recreate or scale it here

