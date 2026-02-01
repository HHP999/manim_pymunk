
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints  import RatchetJoint
from pymunk import Space
from typing import Optional

class VRatchetJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        phase: float = 0.0,
        ratchet: float = PI / 4,
        show_connection: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Ratchet specific properties
        # ratchet: the angle distance between "clicks"
        # phase: the initial angular offset
        self.phase = phase
        self.ratchet = ratchet

        self.show_connection = show_connection
        self.connection_line = None
        self.constraint: Optional[RatchetJoint] = None

    def install(self, space: Space):
        """Install the rotary ratchet constraint into the physics space."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VRatchetJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk RatchetJoint
        self.constraint = RatchetJoint(a_body, b_body, self.phase, self.ratchet)

        # 2. Initialize Visuals
        # Like GearJoint, this is an abstract angular constraint.
        # We can draw a dashed line between centers to indicate they are linked.
        if self.show_connection:
            self.connection_line = DashedLine(
                self.a_mob.get_center(),
                self.b_mob.get_center(),
                color=GRAY_C,
                stroke_width=1,
            )
            self.add(self.connection_line)
        else:
            self.connection_line = VMobject()

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Update visual state to track the connected bodies."""
        if not self.constraint:
            return

        if self.show_connection and isinstance(self.connection_line, DashedLine):
            self.connection_line.put_start_and_end_on(
                self.a_mob.get_center(), self.b_mob.get_center()
            )

    @property
    def current_angle(self) -> float:
        """Returns the current angle of the ratchet joint from the physics engine."""
        if self.constraint:
            return self.constraint.angle
        return 0.0

