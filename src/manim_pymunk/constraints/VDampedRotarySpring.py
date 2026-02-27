from manim import *
from typing import Optional
from manim_pymunk.constraints import VConstraint
from pymunk import Space
from pymunk.constraints import DampedRotarySpring


class VDampedRotarySpring(VConstraint):
    """A rotational spring connection is created between the two rigid bodies.
    When the actual relative angle deviates from the target angle,
    the spring torque pulls it back; the damping torque dampens the oscillation.

    Parameters
    ----------
    a_mob
        The first Mobject to be connected. Typically acts as the pivot point or one of the bodies under physical influence.
    b_mob
        The second Mobject to be connected. It is linked to `a_mob` via a physical constraint such as a spring or hinge.
    rest_angle
        The equilibrium angle (in radians). The target angle between the two objects when the system is at rest and no external forces are applied.
    stiffness
        The spring constant (elasticity). A higher value increases the restorative force toward the `rest_angle`, making the spring feel "stiffer."
    damping
        The damping coefficient. Used to simulate energy dissipation (like friction or air resistance). Higher values cause oscillations to decay faster.
    arc_indicator_class
        The class used to visualize the angle (defaults to `Arc`). If set to `None`, no angular arc will be rendered.
    arc_indicator_config
        A dictionary defining the visual style of the arc indicator, including `radius`, `color`, and `stroke_width`.
    connect_line_class
        The class used to draw a connecting line between the two objects (e.g., `Line`). Defaults to `None` for no visible connection.
    connect_line_config
        A dictionary defining the visual style of the connecting line, such as `color` and `stroke_width`.

    Examples
    --------
    .. manim:: VDampedRotarySpringExample

        from manim_pymunk import *

        class VDampedRotarySpringExample(SpaceScene):
            def construct(self):
                floor = Line(LEFT * 10, RIGHT * 10).shift(DOWN*2)

                square_1 = Square().next_to(floor, UP)
                square_2 = Square().move_to(square_1.get_center() + RIGHT * 4)

                constraint = VDampedRotarySpring(
                    square_1,
                    square_2,
                    rest_angle=PI / 4,
                    stiffness=100,
                    damping=1,
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
        rest_angle: float = 0.0,
        stiffness: float = 10.0,
        damping: float = 1.0,
        arc_indicator_class: Optional[Arc] = Arc,
        arc_indicator_config: dict = {"radius": 0.1, "color": RED, "stroke_width": 4},
        connect_line_class: Optional[Line] = None,
        connect_line_config: dict = {"color": YELLOW, "stroke_width": 2},
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        self.rest_angle = rest_angle
        self.stiffness = stiffness
        self.damping = damping

        # 样式配置存储
        self.arc_indicator_class = arc_indicator_class
        self.arc_indicator_config = arc_indicator_config
        self.connect_line_class = connect_line_class
        self.connect_line_config = connect_line_config

        # 视觉组件占位
        self.arc_a: Optional[VMobject] = None
        self.arc_b: Optional[VMobject] = None
        self.conn_line: Optional[VMobject] = None
        self.constraint: Optional[DampedRotarySpring] = None
        self.__check_data()

    def __check_data(self):
        """Verify the validity of constraint parameters."""

        if self.a_mob is None or self.b_mob is None:
            raise ValueError(
                "Constraints cannot be created without both a_mob and b_mob."
            )

        dist = np.linalg.norm(self.a_mob.get_center() - self.b_mob.get_center())

        if dist < 0.000001:
            if self.connect_line_class is not None:
                raise ValueError(
                    f"Points {self.a_mob} and {self.b_mob} are at the same location ({dist:.8f}). "
                    "Connecting them with a line makes no sense."
                )

    def install(self, space: Space):
        """Initialization of physics and visualization components"""

        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError(
                "VDampedRotarySpring 连接的物体必须先执行 add_dynamic_body"
            )

        self.constraint = DampedRotarySpring(
            a_body, b_body, self.rest_angle, self.stiffness, self.damping
        )

        # 初始化连接线
        if self.connect_line_class:
            self.conn_line = self.connect_line_class(
                self.a_mob.get_center(),
                self.b_mob.get_center(),
                **self.connect_line_config,
            )
            self.add(self.conn_line)

        # 初始化两个弧形指示器
        if self.arc_indicator_class:
            self.arc_a = self.arc_indicator_class(
                angle=self.rest_angle, **self.arc_indicator_config
            )
            self.arc_b = self.arc_indicator_class(
                angle=self.rest_angle, **self.arc_indicator_config
            )
            self.add(self.arc_a, self.arc_b)

        # 3. 注入物理世界
        space.add(self.constraint)

        # 4. 绑定更新器
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Visual control updater"""

        if not self.constraint:
            return

        if self.conn_line:
            self.conn_line.put_start_and_end_on(
                self.a_mob.get_center(), self.b_mob.get_center()
            )

        body_a = self.constraint.a
        body_b = self.constraint.b

        # 2. 获取 Manim 坐标
        pos_a = np.array([body_a.position.x, body_a.position.y, 0])
        pos_b = np.array([body_b.position.x, body_b.position.y, 0])

        # 3. 计算连线几何信息
        diff = pos_b - pos_a
        dist = np.linalg.norm(diff)

        # 防止重合导致的计算除零错误
        if dist < 0.001:
            unit_vec = np.array([1, 0, 0])
        else:
            unit_vec = diff / dist

        # 4. 计算角度差
        rel_angle = body_b.angle - body_a.angle
        display_angle = rel_angle if abs(rel_angle) > 0.005 else 0.005

        # 5. 更新弧形指示器
        buff = 0.3
        line_angle = np.arctan2(unit_vec[1], unit_vec[0])  # 连线的绝对角度

        if self.arc_a:
            new_arc_a = self.arc_indicator_class(
                angle=display_angle, **self.arc_indicator_config
            )
            target_pos_a = pos_a - unit_vec * (self.a_mob.get_width() / 2 + buff)
            new_arc_a.move_to(target_pos_a)
            new_arc_a.rotate(
                line_angle - display_angle / 2 + PI, about_point=target_pos_a
            )
            self.arc_a.become(new_arc_a)

        if self.arc_b:
            new_arc_b = self.arc_indicator_class(
                angle=-display_angle, **self.arc_indicator_config
            )
            target_pos_b = pos_b + unit_vec * (self.b_mob.get_width() / 2 + buff)
            new_arc_b.move_to(target_pos_b)
            new_arc_b.rotate(
                line_angle - (-display_angle) / 2, about_point=target_pos_b
            )
            self.arc_b.become(new_arc_b)
