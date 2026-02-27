from manim import *
from manim_pymunk.constraints.constraint import VConstraint
import pymunk
from typing import Tuple
from manim.mobject.mobject import Mobject

from manim_pymunk.space import VSpace

from manim_pymunk.utils.logger_tool import manim_pymunk_logger


class SpaceScene(ZoomedScene):
    """A rotational spring connection is created between the two rigid bodies.
    When the actual relative angle deviates from the target angle,
    the spring torque pulls it back; the damping torque dampens the oscillation.

    Parameters
    ----------
    a_mob
        The first Mobject to be connected. Typically acts as the pivot point or one of the bodies under physical influence.
    b_mob
        The second Mobject to be connected. It is linked to `a_mob` via a physical constraint such as a spring or hinge.

    Examples
    --------
    .. manim:: SpaceSceneExample

        import random

        from manim import *
        from manim_pymunk import *
        from pathlib import Path
        import svgelements as se

        class Car(VGroup):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                width, height, wheel_radius = 2.5, 1.5, 1
                self.body = Rectangle(width=width, height=height, color=BLUE, fill_opacity=0.8)

                # 锚点获取
                p_B_body = self.body.get_corner(DL)
                p_C_body = self.body.get_corner(DR)

                # 车轮创建
                self.back_wheel = Circle(radius=wheel_radius, color=WHITE, fill_opacity=1)
                self.back_wheel.move_to(p_B_body + LEFT * 1.5 + DOWN * 0.5)

                self.front_wheel = Circle(radius=wheel_radius, color=WHITE, fill_opacity=1)
                self.front_wheel.move_to(p_C_body + RIGHT * 1.5 + DOWN * 0.5)

                # --- 新增：直角三角形铲斗 ABC ---
                # B点位置：前轮中心右侧 0.5
                pos_B = (
                    self.front_wheel.get_center() + (wheel_radius + 0.3) * RIGHT + DOWN * 0.5
                )
                # C点位置：B点右侧 0.8 (水平)
                pos_C = pos_B + RIGHT * 1.8
                # A点位置：B点上方 0.6 (垂直)
                pos_A = pos_B + UP * 1

                self.shovel = Polygon(pos_A, pos_B, pos_C, color=ORANGE, fill_opacity=0.9)
                print(self.shovel.get_vertices())
                self.add(self.body, self.back_wheel, self.front_wheel, self.shovel)

            def add_constraints(self, static_body):
                # 1. 基础点位获取
                # 统一获取中心点，用于计算相对偏移
                body_center = self.body.get_center()
                # 1. 计算相对偏移（局部坐标）
                # 这样无论 move_to 到哪，结果都是固定的偏移量
                loc_A = self.body.get_corner(UL) - body_center
                loc_B = self.body.get_corner(DL) - body_center
                loc_C = self.body.get_corner(DR) - body_center
                loc_D = self.body.get_corner(UR) - body_center

                # 铲斗顶点坐标（用于物理锚点参考）
                # 注意：Manim-Pymunk 内部需要相对于各自 Mobject 中心的相对坐标
                s_A = self.shovel.get_vertices()[0]
                s_B = self.shovel.get_vertices()[1]
                print(self.shovel.get_vertices())

                # 2. 原有的车轮旋转销钉 (A-后轮, D-前轮)
                pivots = [
                    VPinJoint(
                        self.body,
                        self.back_wheel,
                        anchor_a_local=loc_A,
                        anchor_b_local=ORIGIN,
                        connect_line_class=Line,
                        anchor_a_appearance=VMobject(),
                        anchor_b_appearance=VMobject(),
                    ),
                    VPinJoint(
                        self.body,
                        self.front_wheel,
                        anchor_a_local=loc_D,
                        anchor_b_local=ORIGIN,
                        connect_line_class=Line,
                        anchor_a_appearance=VMobject(),
                        anchor_b_appearance=VMobject(),
                    ),
                ]

                shovel_locks = [
                    VPinJoint(
                        self.body,
                        self.shovel,
                        anchor_a_local=loc_C,
                        anchor_b_local=s_A - self.shovel.get_center(),
                        anchor_a_appearance=VMobject(),
                        anchor_b_appearance=VMobject(),
                    ),
                    VPinJoint(
                        self.body,
                        self.shovel,
                        anchor_a_local=loc_D,
                        anchor_b_local=s_A - self.shovel.get_center(),
                        anchor_a_appearance=VMobject(),
                        anchor_b_appearance=VMobject(),
                    ),
                    VPinJoint(
                        self.body,
                        self.shovel,
                        anchor_a_local=loc_C,
                        anchor_b_local=s_B - self.shovel.get_center(),
                        anchor_a_appearance=VMobject(),
                        anchor_b_appearance=VMobject(),
                    ),
                    VPinJoint(
                        self.body,
                        self.shovel,
                        anchor_a_local=loc_D,
                        anchor_b_local=s_B - self.shovel.get_center(),
                        # connect_line_class=Line,
                        anchor_a_appearance=VMobject(),
                        anchor_b_appearance=VMobject(),
                    ),
                ]

                rest_dist = np.linalg.norm(
                    self.back_wheel.get_center() - self.front_wheel.get_center()
                )
                horizontal_spring = VDampedSpring(
                    self.back_wheel,
                    self.front_wheel,
                    rest_length=rest_dist,
                    stiffness=500,
                    damping=30,
                    connect_line_config={"turns": 18, "color": RED, "stroke_width": 4},
                )

                suspensions = [
                    VDampedSpring(
                        self.body,
                        self.back_wheel,
                        anchor_a_local=loc_B,
                        rest_length=np.linalg.norm(
                            self.body.get_corner(DL) - self.back_wheel.get_center()
                        ),
                        stiffness=400,
                        damping=15,
                        connect_line_config={"turns": 8, "color": RED, "stroke_width": 4},
                    ),
                    VDampedSpring(
                        self.body,
                        self.front_wheel,
                        anchor_a_local=loc_C,
                        rest_length=np.linalg.norm(
                            self.body.get_corner(DR) - self.front_wheel.get_center()
                        ),
                        stiffness=400,
                        damping=15,
                        connect_line_config={"turns": 8, "color": RED, "stroke_width": 4},
                    ),
                ]

                # 5. 马达
                motors = [
                    VSimpleMotor(self.body, self.back_wheel, rate=15, max_torque=1000),
                    VSimpleMotor(self.body, self.front_wheel, rate=15, max_torque=1000),
                ]

                # 6. 旋转限制 (修正版)
                # 注意：我们需要限制的是 body 相对于“世界(静态空间)”的角度
                # 而不是相对于会旋转的轮子
                rotary_limits = [
                    VRotaryLimitJoint(
                        self.body,
                        static_body,  # 关键：连接到静态背景
                        min_angle=-60 * DEGREES,
                        max_angle=60 * DEGREES,
                    )
                ]
                return [
                    *rotary_limits,
                    *suspensions,
                    *pivots,
                    *shovel_locks,
                    horizontal_spring,
                    *motors,
                ]


        class SpaceSceneExample(SpaceScene):
            def construct(self):
                floor = Line(start=LEFT * 2, end=RIGHT * 10, stroke_width=12, color=RED)
                floor.to_edge(DOWN, buff=0.1)

                slope = VMobjectFromSVGPath(
                    se.Path(
                        "M0 11C0 7.3 0 3.7 0 0 27.3 0 54.7 0 82 0 78 0 77 1 72 3 68 4 68 3 64 2 60 4 57 2 51 1 43 2 40 4 38 6 34 11 31 6 26 6 20 5 15 7 11 10 8 11 4 11 0 11"
                    )
                )
                slope.set_stroke(color=WHITE, width=10).set_fill(
                    color=BLACK, opacity=0.8
                ).next_to(floor, UP, buff=0).scale(4)

                stone_group = VGroup()

                slope_anchors = slope.get_anchors()
                stone_radius = 0.4
                for i in range(0, len(slope_anchors)):
                    dot = Dot(slope_anchors[i], color=RED, radius=stone_radius)
                    dot.shift(UP * stone_radius)
                    stone_group.add(dot)

                rock_group = VGroup()

                x_min = slope.get_left()[0]
                x_max = slope.get_right()[0]
                y_min = slope.get_top()[1] + 10
                y_max = slope.get_top()[1] + 15

                rock_template = Line(start=ORIGIN, end=RIGHT * 0.5, stroke_width=40, color=RED)

                for _ in range(100):
                    rand_x = random.uniform(x_min, x_max)
                    rand_y = random.uniform(y_min, y_max)
                    new_rock = rock_template.copy()
                    new_rock.move_to([rand_x, rand_y, 0])
                    new_rock.rotate(random.uniform(0, PI * 0.25))
                    rock_group.add(new_rock)

                car = Car().shift(LEFT * 2).move_to(slope.get_start() + RIGHT * 5 + UP * 3)

                self.add_static_body(floor, slope)
                self.add_dynamic_body(*stone_group, *rock_group)
                self.add_dynamic_body(car.shovel, density=0.2)
                self.add_dynamic_body(car.body, density=5)
                self.add_dynamic_body(car.back_wheel, car.front_wheel, density=2, friction=0.8)
                self.add_shapes_filter(
                    car.body, car.back_wheel, car.front_wheel, car.shovel, group=123
                )
                self.add_constraints(*car.add_constraints(static_body=slope))

                self.add(self.camera.frame)
                self.camera.frame.move_to(car)
                self.camera.frame.scale(2)
                self.camera.frame.add_updater(lambda m: m.move_to(car))

                # self.draw_debug_img(xlim=(-200, 200), ylim=(-1, 50))
                self.wait(3)
    """

    def __init__(self, gravity: Tuple[float, float] = (0, -9.81), **kwargs):
        super().__init__(**kwargs)
        self.vspace = VSpace(gravity=gravity)
        manim_pymunk_logger.debug("SpaceScene initional~")

    def setup(self):
        """Instance initialization configuration.
        Automatically add physical space to the scene and start the physics state updater.
        """
        self.add(self.vspace)
        self.vspace.init_updater()

    def add_shapes_filter(
        self,
        *mobs,
        group: int = 0,
        categories: int = 4294967295,
        mask: int = 4294967295,
    ):
        """Sets the collision filter for the shapes associated with the given Mobjects.
        This determines which shapes can collide with each other based on groups,
        categories, and masks.

        Parameters
        ----------
        mobs
            The Mobjects whose physical shapes will have the filter applied.
        group
            A group ID. Shapes in the same non-zero group do not collide.
            Useful for creating multi-part objects where internal parts ignore each other.
        categories
            A bitmask of the categories this shape belongs to. Default is all categories (0xFFFFFFFF).
        mask
            A bitmask of the categories this shape can collide with. Default is all categories (0xFFFFFFFF).
        """
        for mob in mobs:
            self.vspace._add_shape_filter(mob, group, categories, mask)

    def add_static_body(
        self,
        *mobs,
        family_members=False,
        is_solid=True,
        # shapes 相关
        elasticity: float = 0.8,
        friction: float = 0.8,
        density: float = 1.0,
        sensor: bool = False,
        surface_velocity: Tuple[float, float] = (0.0, 0.0),
        # body 相关
        center_of_gravity: Tuple[float, float] = (0.0, 0.0),
        velocity: Tuple[float, float] = (0.0, 0.0),
        angular_velocity: float = 0.0,
    ):
        """Adds Mobjects to the physical space as static bodies.
        Static bodies do not move under the influence of gravity or collisions
        and are typically used for environment boundaries like floors and walls.

        Parameters
        ----------
        mobs
            The Mobjects to be treated as static physical objects.
        family_members
            If True, all sub-mobjects (children) will also be added to the physical space.
        is_solid
            Determines if the body is solid. If False, it might be treated as a hollow
            boundary or wireframe depending on the implementation.
        elasticity
            The elasticity (restitution) of the shape. A value of 0.0 means no bounce,
            while 1.0 represents a perfectly elastic collision.
        friction
            The friction coefficient. Determines how much the object resists
            sliding along surfaces.
        density
            The density of the object. For static bodies, this is primarily used
            to calculate mass if the body is ever converted to dynamic.
        sensor
            If True, the shape will detect collisions but will not produce a
            physical collision response (objects will pass through it).
        surface_velocity
            The surface velocity of the shape. Useful for creating conveyor
            belt effects.
        center_of_gravity
            The center of gravity relative to the Mobject's center.
        velocity
            The initial linear velocity of the body. Though static, this can
            affect how objects bounce off it.
        angular_velocity
            The initial angular velocity of the body.
        """
        self.add(*mobs)
        for mob in mobs:
            targets = mob.family_members_with_points() if family_members else [mob]
            for target in targets:
                # 显式传递每一个变量
                self.vspace.set_body_and_shapes(
                    target,
                    body_type=pymunk.Body.STATIC,
                    is_solid=is_solid,
                    # shapes 映射
                    elasticity=elasticity,
                    friction=friction,
                    density=density,
                    sensor=sensor,
                    surface_velocity=surface_velocity,
                    # body 映射
                    center_of_gravity=center_of_gravity,
                    velocity=velocity,
                    angular_velocity=angular_velocity,
                )

    def add_dynamic_body(
        self,
        *mobs,
        family_members=False,
        is_solid=True,
        # shapes 相关
        elasticity: float = 0.8,
        friction: float = 0.8,
        density: float = 1.0,
        sensor: bool = False,
        surface_velocity: Tuple[float, float] = (0.0, 0.0),
        # body 相关
        center_of_gravity: Tuple[float, float] = (0.0, 0.0),
        velocity: Tuple[float, float] = (0.0, 0.0),
        angular_velocity: float = 0.0,
    ):
        """Adds Mobjects to the physical space as static bodies.
        Static bodies do not move under the influence of gravity or collisions
        and are typically used for environment boundaries like floors and walls.

        Parameters
        ----------
        mobs
            The Mobjects to be treated as static physical objects.
        family_members
            If True, all sub-mobjects (children) will also be added to the physical space.
        is_solid
            Determines if the body is solid. If False, it might be treated as a hollow
            boundary or wireframe depending on the implementation.
        elasticity
            The elasticity (restitution) of the shape. A value of 0.0 means no bounce,
            while 1.0 represents a perfectly elastic collision.
        friction
            The friction coefficient. Determines how much the object resists
            sliding along surfaces.
        density
            The density of the object. For static bodies, this is primarily used
            to calculate mass if the body is ever converted to dynamic.
        sensor
            If True, the shape will detect collisions but will not produce a
            physical collision response (objects will pass through it).
        surface_velocity
            The surface velocity of the shape. Useful for creating conveyor
            belt effects.
        center_of_gravity
            The center of gravity relative to the Mobject's center.
        velocity
            The initial linear velocity of the body. Though static, this can
            affect how objects bounce off it.
        angular_velocity
            The initial angular velocity of the body.
        """
        self.add(*mobs)
        for mob in mobs:
            targets = mob.family_members_with_points() if family_members else [mob]
            for target in targets:
                # 显式传递每一个变量
                self.vspace.set_body_and_shapes(
                    target,
                    body_type=pymunk.Body.DYNAMIC,
                    is_solid=is_solid,
                    # shapes 映射
                    elasticity=elasticity,
                    friction=friction,
                    density=density,
                    sensor=sensor,
                    surface_velocity=surface_velocity,
                    # body 映射
                    center_of_gravity=center_of_gravity,
                    velocity=velocity,
                    angular_velocity=angular_velocity,
                )

    def add_kinematic_body(
        self,
        *mobs,
        family_members=False,
        is_solid=True,
        # shapes 相关
        elasticity: float = 0.8,
        friction: float = 0.8,
        density: float = 1.0,
        sensor: bool = False,
        surface_velocity: Tuple[float, float] = (0.0, 0.0),
        # body 相关
        center_of_gravity: Tuple[float, float] = (0.0, 0.0),
        velocity: Tuple[float, float] = (0.0, 0.0),
        angular_velocity: float = 0.0,
    ):
        """Adds Mobjects to the physical space as static bodies.
        Static bodies do not move under the influence of gravity or collisions
        and are typically used for environment boundaries like floors and walls.

        Parameters
        ----------
        mobs
            The Mobjects to be treated as static physical objects.
        family_members
            If True, all sub-mobjects (children) will also be added to the physical space.
        is_solid
            Determines if the body is solid. If False, it might be treated as a hollow
            boundary or wireframe depending on the implementation.
        elasticity
            The elasticity (restitution) of the shape. A value of 0.0 means no bounce,
            while 1.0 represents a perfectly elastic collision.
        friction
            The friction coefficient. Determines how much the object resists
            sliding along surfaces.
        density
            The density of the object. For static bodies, this is primarily used
            to calculate mass if the body is ever converted to dynamic.
        sensor
            If True, the shape will detect collisions but will not produce a
            physical collision response (objects will pass through it).
        surface_velocity
            The surface velocity of the shape. Useful for creating conveyor
            belt effects.
        center_of_gravity
            The center of gravity relative to the Mobject's center.
        velocity
            The initial linear velocity of the body. Though static, this can
            affect how objects bounce off it.
        angular_velocity
            The initial angular velocity of the body.
        """
        self.add(*mobs)
        for mob in mobs:
            targets = mob.family_members_with_points() if family_members else [mob]
            for target in targets:
                # 显式传递每一个变量
                self.vspace.set_body_and_shapes(
                    target,
                    body_type=pymunk.Body.KINEMATIC,
                    is_solid=is_solid,
                    # shapes 映射
                    elasticity=elasticity,
                    friction=friction,
                    density=density,
                    sensor=sensor,
                    surface_velocity=surface_velocity,
                    # body 映射
                    center_of_gravity=center_of_gravity,
                    velocity=velocity,
                    angular_velocity=angular_velocity,
                )

    def add_constraints(self, *mobs: VConstraint):
        """Adds constraint Mobjects to the scene and installs them into the physical space.
        This method ensures that the constraints (such as springs, joints, or motors)
        are both visually rendered in Manim and physically simulated in Pymunk.

        Parameters
        ----------
        mobs
            The VConstraint objects to be added. Each must implement an `install`
            method to link with the physical space.
        """
        self.add(*mobs)
        for mob in mobs:
            mob.install(space=self.vspace.space)

    def active_body(self, *mobs: Mobject) -> None:
        """Activates the physical bodies of the given Mobjects if they are sleeping.
        In physics simulations, bodies that have come to rest are often put to 'sleep'
        to save computation. This method forces those bodies back into an active state.

        Parameters
        ----------
        mobs
            The Mobjects whose associated physical bodies should be activated.
            This includes all sub-mobjects within the family tree of each provided Mobject.
        """
        for mob in mobs:
            family = mob.family_members_with_points()
            for sub_mob in family:
                if (
                    hasattr(sub_mob, "body")
                    and sub_mob.body.body_type is pymunk.Body.DYNAMIC
                    and sub_mob.body.is_sleeping
                ):
                    sub_mob.body.activate()

    def sleep_body(self, *mobs: Mobject) -> None:
        """Forces the physical bodies of the given Mobjects into a sleeping state.
        Sleeping bodies are removed from the physics simulation update loop until
        they are touched by another active body or manually activated, which
        helps reduce CPU usage.

        Parameters
        ----------
        mobs
            The Mobjects whose associated physical bodies should be put to sleep.
            This iterates through all sub-mobjects within the family tree of
            each provided Mobject.
        """
        for mob in mobs:
            # 解决组的问题
            family = mob.family_members_with_points()
            for sub_mob in family:
                if (
                    hasattr(sub_mob, "body")
                    and sub_mob.body.body_type is pymunk.Body.DYNAMIC
                ):
                    sub_mob.body.sleep()

    def draw_debug_img(self, option: int = None, xlim=(-8, 8), ylim=(-5, 5)) -> None:
        """Pops up a Matplotlib window to render a debug view of the physical space.
        This is an essential diagnostic tool used to verify if collision shapes,
        constraints, and pivots are correctly aligned when they are not behaving
        as expected in the Manim render.

        .. note::
            This method will block the execution of the program until the
            pop-up window is manually closed.

        Parameters
        ----------
        option
            Pymunk debug draw options (e.g., `pymunk.SpaceDebugDrawOptions`).
            Determines what physical elements (shapes, constraints, collision points) are visible.
        xlim
            The display range for the X-axis in the plot.
        ylim
            The display range for the Y-axis in the plot.
        """
        import matplotlib.pyplot as plt
        import pymunk.matplotlib_util
        import matplotlib

        matplotlib.use("TkAgg")

        _, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_aspect("equal")

        draw_options = pymunk.matplotlib_util.DrawOptions(ax)
        if option is not None:
            draw_options.flags = option
        else:
            draw_options.flags = (
                pymunk.SpaceDebugDrawOptions.DRAW_SHAPES
                | pymunk.SpaceDebugDrawOptions.DRAW_COLLISION_POINTS
                # | pymunk.SpaceDebugDrawOptions.DRAW_CONSTRAINTS
            )

        self.vspace.space.debug_draw(draw_options)

        # block=True 会阻塞程序直到你手动关闭窗口
        plt.show(block=True)

    @staticmethod
    def get_body(mob: Mobject) -> pymunk.Body | None:
        """Extracts the bound Pymunk Body object from a Manim Mobject.

        This method retrieves the physical body associated with the Mobject,
        allowing for direct manipulation of physical properties like mass or velocity.

        Parameters
        ----------
        mob
            The target Mobject to extract the body from.

        Returns
        -------
        pymunk.Body | None
            The bound physical body.

        Raises
        ------
        RuntimeError
            If the Mobject has not been added to the physical space yet.
        """
        if hasattr(mob, "body"):
            return mob.body
        else:
            raise RuntimeError("Please add 'mobject' to the space first!")

    @staticmethod
    def get_shapes(mob: Mobject) -> list[pymunk.Shape] | None:
        """Retrieves the list of Pymunk Shape objects associated with a Mobject.

        Shapes define the collision boundaries of a body. One Mobject may consist
        of multiple physical shapes.

        Parameters
        ----------
        mob
            The Mobject whose physical shapes are to be retrieved.

        Returns
        -------
        list[pymunk.Shape] | None
            A list of Pymunk shapes defining the collision boundaries.

        Raises
        ------
        RuntimeError
            If the Mobject has not been added to the physical space yet.
        """
        if hasattr(mob, "shapes"):
            return mob.shapes
        else:
            raise RuntimeError("Please add 'mobject' to the space first!")
