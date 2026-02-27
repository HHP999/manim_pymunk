from manim import *
from typing import Optional
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import RotaryLimitJoint
from pymunk import Space
import numpy as np


class VRotaryLimitJoint(VConstraint):
    """Initializes a Rotary Limit Joint constraint between two Mobjects.

    This joint constrains the relative rotation between two bodies to stay
    within a specific angular range. It acts as a physical stop when the
    bodies reach the minimum or maximum angle limits.

    Parameters
    ----------
    a_mob
        The first Mobject (the reference body).
    b_mob
        The second Mobject (the constrained body).
    min_angle
        The minimum allowed relative angle (in radians).
    max_angle
        The maximum allowed relative angle (in radians).
    arc_indicator_class
        The Manim class used to visualize the angular limits (typically Arc).
        Set to None to hide the visual representation.
    arc_indicator_config
        Configuration dictionary for the styling of the visual arc.
    Examples
    --------
    .. manim:: VRotaryLimitJointExample

        from manim_pymunk import *

        class VRotaryLimitJointExample(SpaceScene):
            def construct(self):

                static_dot = Dot(ORIGIN)
                square = Square().move_to(static_dot)
                square2 = Square().move_to(static_dot.get_center() + UP * 2).scale(0.5)

                constraints = [
                    VPinJoint(static_dot, square),
                    VPinJoint(
                        square,
                        square2,
                        anchor_a_local=square.get_corner(UR) - square.get_center(),
                        distance=2,
                        connect_line_class=Line,
                    ),
                    VRotaryLimitJoint(
                        static_dot,
                        square2,
                        min_angle=-PI / 6,
                        max_angle=PI / 6,
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
        min_angle: float = -PI / 4,
        max_angle: float = PI / 4,
        arc_indicator_class: Optional[Arc] = Arc,
        arc_indicator_config: dict = {
            "radius": 0.5,
            "color": YELLOW,
            "stroke_width": 2,
        },
        **kwargs,
    ):

        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # 物理限制参数
        self.min_angle = min_angle
        self.max_angle = max_angle

        self.arc_indicator_class = arc_indicator_class
        self.arc_indicator_config = arc_indicator_config

        self.arc_indicator_a: Optional[VMobject] = None
        self.arc_indicator_b: Optional[VMobject] = None
        self.constraint: Optional[RotaryLimitJoint] = None

    def __check_data(self):
        """Verify the validity of constraint parameters."""
        pass

    def install(self, space: Space):
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VRotaryLimitJoint 连接的物体必须先执行 add_dynamic_body")

        self.constraint = RotaryLimitJoint(
            a_body, b_body, self.min_angle, self.max_angle
        )

        if self.arc_indicator_class:
            self.arc_indicator_a = self.arc_indicator_class(
                angle=0, **self.arc_indicator_config
            )
            self.arc_indicator_b = self.arc_indicator_class(
                angle=0, **self.arc_indicator_config
            )
            self.add(self.arc_indicator_a, self.arc_indicator_b)

        space.add(self.constraint)

        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Visual control updater"""
        if not self.constraint:
            return

        a_body = self.constraint.a
        b_body = self.constraint.b
        wa = a_body.position
        wb = b_body.position
        p1 = np.array([wa.x, wa.y, 0])
        p2 = np.array([wb.x, wb.y, 0])

        diff = p2 - p1
        dist = np.linalg.norm(diff)

        if dist < 0.001:
            unit_vec = np.array([1, 0, 0])
        else:
            unit_vec = diff / dist

        rel_angle = b_body.angle - a_body.angle
        display_angle = rel_angle if abs(rel_angle) > 0.005 else 0.005

        buff = 0.3
        line_angle = np.arctan2(unit_vec[1], unit_vec[0])  # 连线的绝对角度

        if self.arc_indicator_a:
            new_arc_a = self.arc_indicator_class(
                angle=display_angle, **self.arc_indicator_config
            )
            target_pos_a = p1 - unit_vec * (self.a_mob.get_width() / 2 + buff)
            new_arc_a.move_to(target_pos_a)

            new_arc_a.rotate(
                line_angle - display_angle / 2 + PI, about_point=target_pos_a
            )
            self.arc_indicator_a.become(new_arc_a)

        if self.arc_indicator_b:
            new_arc_b = self.arc_indicator_class(
                angle=-display_angle, **self.arc_indicator_config
            )
            target_pos_b = p2 + unit_vec * (self.b_mob.get_width() / 2 + buff)
            new_arc_b.move_to(target_pos_b)

            new_arc_b.rotate(
                line_angle - (-display_angle) / 2, about_point=target_pos_b
            )
            self.arc_indicator_b.become(new_arc_b)
