from typing import Optional
from pymunk import Space
from pymunk.constraints import GearJoint
from manim import *
from manim_pymunk.constraints import VConstraint


class VGearJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        phase: float = 0.0,
        ratio: float = 1.0,
        show_indicator: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Gear specific properties
        self.phase = phase
        self.ratio = ratio

        self.show_indicator = show_indicator
        self.constraint: Optional[GearJoint] = None
        self.indicator = None

    def install(self, space: Space):
        """Install the angular gear constraint into the physics space."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VGearJoint connected objects must have a Pymunk body.")

        # 1. Create Pymunk GearJoint
        # Enforces: (angle_b - phase) = ratio * angle_a
        self.constraint = GearJoint(a_body, b_body, self.phase, self.ratio)

        # 2. Initialize Visuals
        # Since GearJoints are abstract angular links, we often don't draw a line.
        # However, we can add a visual indicator (like a dashed connection) if desired.
        if self.show_indicator:
            self.indicator = DashedLine(
                self.a_mob.get_center(), self.b_mob.get_center(), color=GRAY_A
            ).set_opacity(0.5)
            self.add(self.indicator)
        else:
            self.indicator = VMobject()

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Update visual indicators to follow the bodies."""
        if not self.constraint:
            return

        # Update indicator position if it exists
        if self.show_indicator and isinstance(self.indicator, DashedLine):
            self.indicator.put_start_and_end_on(
                self.a_mob.get_center(), self.b_mob.get_center()
            )

    def set_ratio(self, new_ratio: float):
        """Helper to update gear ratio dynamically."""
        if self.constraint:
            self.constraint.ratio = new_ratio
            self.ratio = new_ratio
