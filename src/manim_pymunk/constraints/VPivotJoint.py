from typing import Optional
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints  import PivotJoint
from pymunk import Space

class VPivotJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a: Optional[np.ndarray] = None,
        anchor_b: Optional[np.ndarray] = None,
        pivot: Optional[np.ndarray] = None,
        pivot_appearance: Mobject = Dot(color=WHITE, radius=0.05),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Pymunk supports two ways to init PivotJoint:
        # 1. Provide a single world-space pivot point.
        # 2. Provide two local-space anchor points.
        self.pivot_world = tuple(pivot[:2]) if pivot is not None else None
        self.anchor_a_local = tuple(anchor_a[:2]) if anchor_a is not None else None
        self.anchor_b_local = tuple(anchor_b[:2]) if anchor_b is not None else None

        self.pivot_appearance = pivot_appearance
        self.constraint: Optional[PivotJoint] = None

    def install(self, space: Space):
        """Install the pivot constraint and set up the visual tracker."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VPivotJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk PivotJoint based on provided arguments
        if self.pivot_world is not None:
            # Init via world coordinates
            self.constraint = PivotJoint(a_body, b_body, self.pivot_world)
        elif self.anchor_a_local is not None and self.anchor_b_local is not None:
            # Init via two local anchor points
            self.constraint = PivotJoint(
                a_body, b_body, self.anchor_a_local, self.anchor_b_local
            )
        else:
            # Default to current center of both bodies if nothing provided
            self.constraint = PivotJoint(a_body, b_body, a_body.position)

        # 2. Initial Visual Placement
        # We use anchor_a to track the visual pivot point in the world
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        self.pivot_appearance.move_to([wa.x, wa.y, 0])
        self.add(self.pivot_appearance)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Keep the visual dot at the physical pivot location."""
        if not self.constraint:
            return

        # Body A and Body B's anchors should overlap in world space,
        # so tracking either is fine.
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        self.pivot_appearance.move_to([wa.x, wa.y, 0])
