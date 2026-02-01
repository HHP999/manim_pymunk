
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints  import SimpleMotor
from pymunk import Space
from typing import Optional

class VSimpleMotor(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        rate: float = 1.0,
        max_torque: float = 1000.0,
        show_direction: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Motor properties
        self.rate = rate  # Desired relative angular velocity
        self.max_torque = max_torque

        self.show_direction = show_direction
        self.arrow_indicator = None
        self.constraint: Optional[SimpleMotor] = None

    def install(self, space: Space):
        """Install the motor constraint and initialize the rotation indicator."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VSimpleMotor connected objects must have Pymunk bodies.")

        # 1. Create Pymunk SimpleMotor
        self.constraint = SimpleMotor(a_body, b_body, self.rate)

        # Highly recommended for motors: limit the torque
        self.constraint.max_force = self.max_torque

        # 2. Initialize Visuals
        # A curved arrow to indicate the direction of the motor's drive
        if self.show_direction:
            # Direction of arrow depends on sign of rate
            angle = PI if self.rate >= 0 else -PI
            self.arrow_indicator = CurvedArrow(
                start_point=RIGHT * 0.5,
                end_point=UP * 0.5,
                angle=angle,
                color=GOLD,
                stroke_width=3,
            ).set_opacity(0.6)
            self.add(self.arrow_indicator)
        else:
            self.arrow_indicator = VMobject()

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Keep the indicator centered on the second body (the driven body)."""
        if not self.constraint:
            return

        # Place the motor icon on the body being driven (Body B)
        # or at the midpoint if appropriate.
        self.arrow_indicator.move_to(self.b_mob.get_center())
        # The icon rotates with the body it represents
        self.arrow_indicator.set_angle(self.constraint.b.angle)

    def set_rate(self, new_rate: float):
        """Change the motor speed dynamically."""
        if self.constraint:
            self.constraint.rate = new_rate
            self.rate = new_rate
