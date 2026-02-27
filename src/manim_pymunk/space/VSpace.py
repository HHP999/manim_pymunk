from manim import *
import pymunk
from pymunk import Body, autogeometry
from typing import Callable, Dict, Any, Tuple, Union
import numpy as np
from manim.mobject.geometry.arc import Circle
from manim.mobject.geometry.line import Line
from manim.mobject.mobject import Mobject
from manim.utils.bezier import subdivide_bezier
from manim_pymunk.utils.img_tools import get_normalized_convex_polygons
from manim_pymunk.utils.logger_tool import manim_pymunk_logger

from manim.mobject.opengl.opengl_compatibility import ConvertToOpenGL


class VSpace(Mobject, metaclass=ConvertToOpenGL):
    """Pymunk physical space management is generally not used by users.
    This object has already been created in SpaceScene.

    The Manim visualization manager for a Pymunk physical space.

    The VSpace class encapsulates the Pymunk `Space` object, managing rigid bodies,
    shapes, and constraints within the simulation. It utilizes Manim's updater
    mechanism to synchronize the physical simulation results with Mobject
    visual states in real-time.

    Parameters
    ----------
    gravity
        The gravity acceleration vector $(g_x, g_y)$. Defaults to $(0, -9.81)$.
    sub_step
        The number of sub-steps per frame for physical simulation. Increasing
         this value improves numerical stability and collision accuracy.
        Defaults to 8.

    Examples
    --------
    .. manim:: VSpaceExample

        import random
        from manim_pymunk import *

        class VSpaceExample(SpaceScene):
            def construct(self):

                COLLISION_TYPE = 123
                floor = Line(start=LEFT * 2, end=RIGHT * 10, stroke_width=12, color=RED)
                floor.to_edge(DOWN, buff=0.1)
                self.add_static_body(floor)
                self.vspace._set_collision_type(floor, COLLISION_TYPE)

                stone_num = 40

                stone_temp = Dot(ORIGIN, color=BLUE)
                for _ in range(stone_num):
                    stone = stone_temp.copy().move_to(
                        random.randint(1, 6) * UP + random.randint(-4, 4) * RIGHT
                    )
                    self.add_dynamic_body(stone)
                    self.vspace._set_collision_type(stone, COLLISION_TYPE)

                def post_solve_callback(arbiter, space, data):
                    # 1. 获取总冲量向量
                    impulse = arbiter.total_impulse
                    strength = impulse.length
                    print(strength)
                    if strength > 0.1:
                        self.add_sound(
                            "../../../../examples/assets/click.wav",
                        )
                    return True

                self.vspace._collision_detection_handler(
                    collision_type_a=COLLISION_TYPE,
                    collision_type_b=COLLISION_TYPE,
                    post_solve=post_solve_callback,
                )

                self.wait(3)

    """

    def __init__(
        self, gravity: Tuple[float, float] = (0, -9.81), sub_step: int = 8, **kwargs
    ):
        super().__init__(**kwargs)
        self.space = pymunk.Space()
        self.space.gravity = gravity
        self.space.sleep_time_threshold = 1
        self.sub_step: int = sub_step

    # ================================== init ==================================
    def init_updater(self):
        self.add_updater(self.__step_updater)

    # ================================== updater ==================================
    def __step_updater(self, vspace, dt):
        """Executes a single frame update step for the physical simulation.

        Divides the frame duration into multiple sub-steps and performs incremental
        `step` calculations on the physical space. This significantly improves
        numerical stability and precision, preventing high-speed objects from
        tunneling through boundaries.

        Parameters
        ----------
        vspace
            The VSpace object itself, acting as the controller for the simulation.
        dt
            The time increment for the current frame (in seconds).
        """
        sub_dt = dt / self.sub_step
        for _ in range(self.sub_step):
            vspace.space.step(sub_dt)

    def __simulate_updater(self, mob: Mobject):
        """Synchronizes a Mobject's position and rotation with its associated physical body.

        Reads the latest kinematic state (position and angle) from the Pymunk `Body`
        and updates the Mobject's transform. This ensures that the visual
        representation in Manim stays perfectly aligned with the physics simulation.

        Parameters
        ----------
        mob
            The Manim Mobject to be synchronized. It must have a `.body`
            attribute linked to a Pymunk body.
        """
        x, y = mob.body.position
        mob.move_to((x, y, 0))
        mob.rotate(mob.body.angle - mob.angle)
        mob.angle = mob.body.angle

    # =============================== space  ==================================
    def remove_body_shapes_constraints(
        self, *items: Union[pymunk.Body, pymunk.Shape, pymunk.constraints.Constraint]
    ) -> None:
        """Removes physical bodies, shapes, or constraints from the physical space.

        This method handles the unregistration of Pymunk objects. It is crucial for
        maintaining simulation performance and preventing memory leaks or unexpected
        physical interactions after a Mobject has been removed from the scene.

        Parameters
        ----------
        items
            The Pymunk objects (Body, Shape, or Constraint) to be removed from
            the simulation space.
        """
        self.space.remove(*items)

    def _add_body2space(self, mob: Mobject) -> None:
        """Registers the physical body and shapes of a Mobject into the simulation space.

        If the body is static, only the shapes are added to the space. For dynamic
        or kinematic bodies, both the body and its shapes are added. Additionally,
        this method attaches the simulation updater to the Mobject to ensure its
        visual transform is synchronized with the physical simulation in every frame.

        Parameters
        ----------
        mob
            The Mobject containing `.body` and `.shapes` attributes to be integrated
            into the physical world.
        """
        if mob.body is self.space.static_body:
            self.space.add(*mob.shapes)
        else:
            self.space.add(mob.body)
            self.space.add(*mob.shapes)
        mob.add_updater(self.__simulate_updater)
        mob.body.activate()

    def __set_body(
        self,
        mob: Mobject,
        body_type: int,
        # body 相关
        center_of_gravity: Tuple[float, float],
        velocity: Tuple[float, float],
        angular_velocity: float,
    ) -> None:
        """Initializes and configures the Pymunk physical body for a Mobject.

        This internal method creates a `pymunk.Body` instance, sets its motion
        type (Dynamic, Static, or Kinematic), and applies initial kinematic
        properties such as center of mass, linear velocity, and angular velocity.

        Parameters
        ----------
        mob
            The Mobject to which the physical body will be attached.
        body_type
            The Pymunk body type integer (e.g., `pymunk.Body.DYNAMIC`).
        center_of_gravity
            The center of mass position relative to the Mobject's center $(x, y)$.
        velocity
            The initial linear velocity vector $(v_x, v_y)$ of the body.
        angular_velocity
            The initial angular velocity (in radians per second).
        """

        if not hasattr(mob, "body"):
            mob.set(body=None)
        if not hasattr(mob, "angle"):
            mob.set(angle=0)
        if body_type == pymunk.Body.DYNAMIC:
            mob.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        elif body_type == pymunk.Body.KINEMATIC:
            mob.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        else:
            mob.body = pymunk.Body(body_type=pymunk.Body.STATIC)

        mob.body.position = mob.get_x(), mob.get_y()
        mob.body.center_of_gravity = center_of_gravity
        mob.body.velocity = velocity
        mob.body.angular_velocity = angular_velocity

    def set_body_and_shapes(
        self,
        mob: Mobject,
        body_type: int,
        is_solid: bool,
        # shapes 相关
        elasticity: float,
        friction: float,
        density: float,
        sensor: bool,
        surface_velocity: Tuple[float, float],
        # body 相关
        center_of_gravity: Tuple[float, float],
        velocity: Tuple[float, float],
        angular_velocity: float,
    ) -> None:
        """Sets up both the physical body and its collision shapes for a Mobject.

        This method acts as a high-level initializer that configures the motion
        properties (velocity, gravity center) and the physical material properties
        (friction, elasticity) simultaneously, effectively binding a complete
        physical identity to a visual Mobject.

        Parameters
        ----------
        mob
            The Mobject to be initialized with physical properties.
        body_type
            The Pymunk body type (Dynamic, Static, or Kinematic).
        is_solid
            Whether the shapes are treated as solid objects or hollow boundaries.
        elasticity
            The coefficient of restitution. Controls how much energy is preserved after a collision.
        friction
            The friction coefficient. Controls how much the object resists sliding.
        density
            The density used to calculate mass and moment of inertia based on shape area.
        sensor
            If True, the shapes will trigger collision callbacks but won't cause physical bounces.
        surface_velocity
            A constant velocity applied to the surface of the shape (e.g., for conveyor belts).
        center_of_gravity
            The center of mass relative to the Mobject's center $(x, y)$.
        velocity
            The initial linear velocity vector $(v_x, v_y)$.
        angular_velocity
            The initial angular velocity in radians per second.
        """
        self.__set_body(
            mob,
            body_type,
            center_of_gravity=center_of_gravity,
            velocity=velocity,
            angular_velocity=angular_velocity,
        )
        self.__set_shape(
            mob,
            is_solid,
            elasticity=elasticity,
            friction=friction,
            density=density,
            sensor=sensor,
            surface_velocity=surface_velocity,
        )
        self._add_body2space(mob)

    @staticmethod
    def _set_collision_type(mob: Mobject, collision_type: int):
        """Sets the collision type ID for all physical shapes associated with a Mobject.

        Collision types are user-defined integers used to categorize shapes. By
        assigning types, you can define specific callback functions in a collision
        handler to determine what happens when two shapes of certain types collide.

        Parameters
        ----------
        mob
            The Mobject whose associated physical shapes will be updated.
        collision_type
            An integer ID representing the collision category.
            (e.g., 1 for players, 2 for enemies).
        """
        for shape in mob.shapes:
            shape.collision_type = collision_type

    def _wildcard_collision_handler(
        self,
        collision_type_a: int,
        begin: Callable[[pymunk.Arbiter, pymunk.Space, Dict], bool] = None,
        pre_solve: Callable[[pymunk.Arbiter, pymunk.Space, Dict], bool] = None,
        post_solve: Callable[[pymunk.Arbiter, pymunk.Space, Dict], None] = None,
        separate: Callable[[pymunk.Arbiter, pymunk.Space, Dict], None] = None,
        data: Dict[Any, Any] = None,
    ):
        """Registers a wildcard collision handler for a specific collision type.

        This handler triggers whenever a shape with `collision_type_a` collides
        with any other shape in the space, regardless of the other shape's
        collision type. It is useful for global behaviors, such as playing a
        sound whenever a specific object hits anything.

        Parameters
        ----------
        collision_type_a
            The collision type ID to monitor.
        begin
            Called when two shapes first touch. Returning False ignores the collision.
        pre_solve
            Called every step while shapes are touching, before the collision solver
            runs. Returning False ignores the collision for this step.
        post_solve
            Called every step while shapes are touching, after the collision solver
            runs. Useful for retrieving collision impulse or kinetic energy.
        separate
            Called when two shapes stop touching.
        data
            A custom dictionary passed to all callback functions for state management.

        Returns
        -------
        pymunk.CollisionHandler
            The registered collision handler object.
        """
        handler = self.space.add_wildcard_collision_handler(collision_type_a)
        if begin:
            handler.begin = begin
        if pre_solve:
            handler.pre_solve = pre_solve
        if post_solve:
            handler.post_solve = post_solve
        if separate:
            handler.separate = separate
        if data:
            handler.data.update(data)

        return handler

    def _collision_detection_handler(
        self,
        collision_type_a: int,
        collision_type_b: int,
        begin: Callable[[pymunk.Arbiter, pymunk.Space, Dict], bool] = None,
        pre_solve: Callable[[pymunk.Arbiter, pymunk.Space, Dict], bool] = None,
        post_solve: Callable[[pymunk.Arbiter, pymunk.Space, Dict], None] = None,
        separate: Callable[[pymunk.Arbiter, pymunk.Space, Dict], None] = None,
        data: Dict[Any, Any] = None,
    ):
        """Registers a collision handler between two specific collision types.

        This method defines custom callback logic for when a shape of type A
        interacts with a shape of type B. It allows for fine-grained control over
        physics responses, such as triggering events, modifying friction during
        contact, or preventing specific objects from bouncing.

        Parameters
        ----------
        collision_type_a
            The first specific collision type ID.
        collision_type_b
            The second specific collision type ID.
        begin
            Called when the two shapes first make contact. Must return True to
            process the collision physically, or False to ignore it.
        pre_solve
            Called in each step while the shapes are touching, before the solver runs.
            Useful for overriding collision parameters like friction or surface velocity.
        post_solve
            Called in each step while the shapes are touching, after the solver runs.
            Commonly used to calculate collision impulses or impact energy.
        separate
            Called at the final step when the two shapes stop touching.
        data
            A custom dictionary for storing persistent state information accessible
            within the callbacks.

        Returns
        -------
        pymunk.CollisionHandler
            The registered collision handler object.
        """
        print(type(self.space))
        handler = self.space.add_collision_handler(collision_type_a, collision_type_b)

        if begin:
            handler.begin = begin
        if pre_solve:
            handler.pre_solve = pre_solve
        if post_solve:
            handler.post_solve = post_solve
        if separate:
            handler.separate = separate

        if data:
            handler.data.update(data)

        return handler

    # =============================== body ==================================
    @staticmethod
    def apply_force_at_local_point(
        mob: Mobject,
        force: Tuple[float, float, float],
        point: Tuple[float, float, float] = (0, 0, 0),
    ) -> None:
        """Applies a force to a Mobject's physical body at a point defined in local coordinates.

        The force is applied relative to the body's current orientation. If the point
        is not the center of gravity, it will also generate a torque, causing the
        object to rotate.

        Parameters
        ----------
        mob
            The Mobject whose physical body will receive the force.
        force
            The force vector $(f_x, f_y, f_z)$ to apply. Note that Pymunk
            operates in 2D, so the z-component is typically ignored.
        point
            The offset from the body's center of gravity $(x, y, z)$ where
            the force is applied, in local coordinates.
        """

        mob.body.apply_force_at_local_point(force=force[:2], point=point[:2])

    @staticmethod
    def apply_force_at_world_point(
        mob: Mobject,
        force: Tuple[float, float, float],
        point: Tuple[float, float, float] = (0, 0, 0),
    ) -> None:
        """Applies a force to a Mobject's physical body at a point defined in world coordinates.

        The force vector is applied at an absolute position in the scene. If the
        point does not coincide with the body's center of gravity, it will generate
        torque and cause the body to rotate. This is useful for external influences
        that occur at specific scene locations.

        Parameters
        ----------
        mob
            The Mobject whose physical body will receive the force.
        force
            The force vector $(f_x, f_y, f_z)$ to apply. Note that Pymunk
            typically ignores the z-component.
        point
            The absolute position in the world (scene) coordinates where the
            force is applied. Defaults to the origin $(0, 0, 0)$.
        """
        mob.body.apply_force_at_world_point(force=force[:2], point=point[:2])

    @staticmethod
    def apply_impulse_at_local_point(
        mob: Mobject,
        impulse: Tuple[float, float, float],
        point: Tuple[float, float, float] = (0, 0, 0),
    ) -> None:
        """Applies an instantaneous impulse to a Mobject's physical body at a local point.

        Impulses cause an immediate change in velocity (linear and angular) without
        requiring time to elapse, simulating effects like a sudden hit or explosion.
        The point is defined relative to the body's current position and orientation.

        Parameters
        ----------
        mob
            The Mobject whose physical body will receive the impulse.
        impulse
            The impulse vector $(i_x, i_y, i_z)$ to apply. The z-component
            is typically ignored in 2D physics.
        point
            The offset from the body's center of gravity $(x, y, z)$ where the
            impulse is applied, in local coordinates.
        """
        mob.body.apply_impulse_at_local_point(impulse=impulse[:2], point=point[:2])

    @staticmethod
    def apply_impulse_at_world_point(
        mob: Mobject,
        impulse: tuple[float, float, float],
        point: Tuple[float, float, float] = (0, 0, 0),
    ) -> None:
        """Applies an instantaneous impulse to a Mobject's physical body at a world coordinate.

        The impulse vector is applied at an absolute position in the scene. This causes
        an immediate change in the body's linear and angular velocity. If the
        application point is offset from the body's center of mass, the body will
        begin to rotate.

        Parameters
        ----------
        mob
            The Mobject whose physical body will receive the impulse.
        impulse
            The impulse vector $(i_x, i_y, i_z)$ to apply. The z-component
            is typically ignored in 2D physics.
        point
            The absolute position in world (scene) coordinates where the
            impulse is applied. Defaults to the origin $(0, 0, 0)$.
        """
        mob.body.apply_impulse_at_world_point(impulse=impulse[:2], point=point[:2])

    @staticmethod
    def local_to_world(
        mob: Mobject, point: Tuple[float, float, float] = (0, 0, 0)
    ) -> Tuple[float, float, float]:
        world_pos = mob.body.local_to_world(point[:2])
        return (*world_pos, 0)

    @staticmethod
    def world_to_local(
        mob: Mobject, point: Tuple[float, float, float] = (0, 0, 0)
    ) -> Tuple[float, float, float]:
        local_pos = mob.body.world_to_local(point[:2])
        return (*local_pos, 0)

    @staticmethod
    def set_position_func(
        mob: Mobject, callback: Callable[[pymunk.Body, float], None] = None
    ):
        """Assigns a custom position update callback to a Mobject's physical body.

        By default, Pymunk updates a body's position based on its velocity. This
        method allows you to override that behavior with custom logic. The callback
        is executed during every physical simulation step.

        Parameters
        ----------
        mob
            The Mobject whose physical body's position update logic will be customized.
        callback
            A function with the signature `def callback(body: pymunk.Body, dt: float)`.
            If None, the default Pymunk position update logic is restored.
        """
        if callback:
            mob.body.position_func = callback

    @staticmethod
    def set_velocity_func(
        mob: Mobject,
        callback: Callable[[Body, tuple[float, float], float, float], None] = None,
    ):
        """Assigns a custom velocity update callback to a Mobject's physical body.

        This method overrides how Pymunk calculates velocity in each step. It is commonly
        used to implement specialized physical effects such as custom air resistance (drag),
        planetary gravity, or specific damping behaviors that differ from the global space settings.

        Parameters
        ----------
        mob
            The Mobject whose physical body's velocity logic will be customized.
        callback
            A function with the signature:
            `def callback(body: Body, gravity: Tuple[float, float], damping: float, dt: float)`
            If None, the default Pymunk velocity update logic is restored.
        """
        if callback:
            mob.body.velocity_func = callback

    @staticmethod
    def velocity_at_local_point(
        mob: Mobject, point: Tuple[float, float, float] = (0, 0, 0)
    ) -> Tuple[float, float, float]:
        velocity = mob.body.velocity_at_local_point(point[:2])
        return (*velocity, 0)

    @staticmethod
    def velocity_at_world_point(
        mob: Mobject, point: Tuple[float, float, float] = (0, 0, 0)
    ) -> Tuple[float, float, float]:
        velocity = mob.body.velocity_at_world_point(point[:2])
        return (*velocity, 0)

    # =============================== shape  ==================================
    def __set_shape(
        self,
        mob: Mobject,
        is_solid: bool = True,  # shapes 映射
        # shapes 相关
        elasticity: float = 0.8,
        friction: float = 0.8,
        density: float = 1.0,
        sensor: bool = False,
        surface_velocity: Tuple[float, float] = (0.0, 0.0),
    ) -> None:
        """Configures and attaches collision shapes to a Mobject's physical body.

        This internal method defines the 'material' and 'boundary' properties of the
        object. It determines how the object bounces, slides, and whether it
        occupies solid space or acts merely as a trigger zone.

        Parameters
        ----------
        mob
            The Mobject to assign physical shapes to. Must already have a `.body`.
        is_solid
            If True, the shape is treated as a solid object. If False, it may be
            treated as a hollow boundary (depending on the geometry type).
        elasticity
            Coefficient of restitution (0.0 to 1.0+). Controls bounciness.
        friction
            Coefficient of friction (0.0 to 1.0+). Controls surface resistance.
        density
            Used to automatically calculate the mass and moment of inertia
            based on the shape's area/volume.
        sensor
            If True, the shape detects collisions (triggers callbacks) but
            produces no physical impact or bounce.
        surface_velocity
            The relative surface velocity. Useful for creating conveyor belt
            effects or moving walkways.
        """

        if not hasattr(mob, "shapes"):
            mob.set(shapes=[])

        if isinstance(mob, ImageMobject):
            self.__calculate_img_shape(mob)
        elif is_solid:
            self.__calculate_solid_shape(mob)
        else:
            self.__calculate_hollow_shape(mob)

        for shape in mob.shapes:
            shape.elasticity = elasticity
            shape.friction = friction
            shape.density = density
            shape.sensor = sensor
            shape.surface_velocity = surface_velocity

    def __calculate_solid_shape(self, mob: Mobject) -> None:
        """Generates Pymunk collision shapes for a solid Mobject.

        This method maps Manim primitives (Circle, Line, Polygon, etc.) to their
        corresponding Pymunk shape types. For complex shapes that are non-convex
        (e.g., a Star or a generic path), it automatically performs convex
        decomposition to ensure accurate physical interaction.

        Parameters
        ----------
        mob
            The VMobject for which collision shapes are generated.

        Note
        ----
        Physical engines generally only support convex polygons. Non-convex
        objects are decomposed into multiple convex sub-shapes attached to
        the same body.
        """
        stroke_width = (mob.stroke_width / 100) * (
            config.frame_height / config.frame_width
        )

        if isinstance(mob, Circle):
            mob.shapes = [
                pymunk.Circle(body=mob.body, radius=mob.radius + stroke_width / 2)
            ]
        elif isinstance(mob, Line):
            center_x, center_y = mob.get_center()[:2]
            start = mob.get_start()
            end = mob.get_end()

            local_a = (start[0] - center_x, start[1] - center_y)
            local_b = (end[0] - center_x, end[1] - center_y)
            mob.shapes = [pymunk.Segment(mob.body, local_a, local_b, stroke_width / 2)]

        #  Polygram, Star, RegularPolygon, VMobject,etc.
        else:
            local_points = self.__get_refined_points(mob, n_divisions=8)

            if len(local_points) < 3:
                return

            # is convex?
            hull = autogeometry.to_convex_hull(local_points, 0.001)
            is_convex = len(hull) == len(local_points)

            if is_convex:
                # is convex
                mob.shapes.append(
                    pymunk.Poly(mob.body, local_points, radius=stroke_width / 2)
                )
            else:
                convex_hulls = self.__concave2convex_refined(
                    mob, n_divisions=8, tolerance=0.01
                )
                for hull_verts in convex_hulls:
                    mob.shapes.append(
                        pymunk.Poly(mob.body, hull_verts, radius=stroke_width / 2)
                    )

    def __calculate_hollow_shape(self, mob: Mobject, n_divisions: int = 4) -> None:
        """Generates Pymunk collision shapes for a hollow Mobject (outline only).

        Instead of a solid polygon, this method constructs a collision boundary using
        multiple `pymunk.Segment` shapes that follow the Mobject's contour. This is
        ideal for creating containers, cages, or hollow structures where other
        physical objects can move inside.

        Parameters
        ----------
        mob
            The VMobject whose stroke/outline will be used to create segments.
        n_divisions
            The subdivision level for Bezier curves. Higher values result in
            smoother boundaries but may impact simulation performance.
        """
        stroke_width = (mob.stroke_width / 100) * (
            config.frame_height / config.frame_width
        )
        refined_points = self.__get_refined_points(mob, n_divisions)
        # Convert to local coordinates relative to the center (required by the physics engine)
        center = mob.get_center()
        refined_points = [(p[0] - center[0], p[1] - center[1]) for p in refined_points]

        n_pts = len(refined_points)
        if n_pts < 2:
            return

        for j in range(n_pts):
            p1 = refined_points[j]
            p2 = refined_points[(j + 1) % n_pts]

            # Filtering: Pymunk will report an error if the two points completely overlap.
            if np.allclose(p1, p2, atol=1e-4):
                continue

            seg = pymunk.Segment(
                mob.body, (p1[0], p1[1]), (p2[0], p2[1]), radius=stroke_width / 2
            )
            mob.shapes.append(seg)

    def __calculate_img_shape(self, mob: ImageMobject) -> None:
        """Generates Pymunk collision shapes from ImageMobject pixel data.

        This method analyzes the image's transparency (alpha channel) or pixel
        contours to extract a representative convex polygon for physical interaction.
        If contour extraction fails or the image is fully opaque, it falls back
        to a standard rectangular bounding box.

        Parameters
        ----------
        mob
            The ImageMobject to process for shape generation.

        Notes
        -----
        For better performance and physical stability, complex image outlines are
        often simplified into low-vertex count convex polygons.
        """
        pixel_array = mob.pixel_array
        polygons_verts = get_normalized_convex_polygons(
            pixel_array,
            base_px_width=512.0,
            target_cell_size=4,
            img_manim_w=mob.width,
            img_manim_h=mob.height,
        )
        if polygons_verts:
            # create polygons
            for poly_verts in polygons_verts:
                mob.shapes.append(pymunk.Poly(mob.body, poly_verts, radius=0.1))
        else:
            # Simple box
            mob.shapes = [
                pymunk.Poly.create_box(
                    mob.body, size=(mob.width, mob.height), radius=0.1
                )
            ]

    @staticmethod
    def __get_refined_points(mob: Mobject, n_divisions: int) -> list:
        """Extracts subdivided sample points from a Mobject for precise collision shape generation.

        This method performs adaptive sampling on the Bezier curves that define a
        VMobject. By increasing the subdivision level, it approximates smooth curves
        with a high-resolution sequence of linear segments. It also includes logic
        to prune redundant points caused by floating-point precision errors.

        Parameters
        ----------
        mob
            The VMobject to be sampled.
        n_divisions
            The subdivision level for each Bezier curve segment. A higher value
            results in a denser point set and smoother physical boundaries.

        Returns
        -------
        list
            A list of subdivided $(x, y)$ coordinate tuples representing the
            sampled path.
        """
        all_points = []
        for submob in mob.family_members_with_points():
            pts = submob.points
            if len(pts) == 0:
                continue

            # bezier divisions
            for i in range(0, len(pts), 4):
                bezier_segment = pts[i : i + 4]
                if len(bezier_segment) < 4:
                    continue
                sub_pts = subdivide_bezier(bezier_segment, n_divisions)
                all_points.extend(sub_pts)

        # 转为 2D 坐标并清洗重复点
        unique_points = []
        for p in all_points:
            p_2d = (float(p[0]), float(p[1]))
            if not unique_points or not np.allclose(p_2d, unique_points[-1], atol=1e-3):
                unique_points.append(p_2d)

        return unique_points

    def __concave2convex_refined(
        self, mob: Mobject, n_divisions: int, tolerance: float
    ):
        """Decomposes a concave polygon into multiple convex polygons for physics processing.

        Since Pymunk and most physics engines only support convex shapes for collision
        detection, this method takes complex non-convex VMobjects (like stars or
        generic paths) and breaks them down into a set of convex sub-polygons.

        Parameters
        ----------
        mob
            The VMobject (e.g., a Star or complex polygon) to be decomposed.
        n_divisions
            The Bezier subdivision level used to sample the Mobject's contour points.
        tolerance
            The decomposition tolerance. Higher values simplify the resulting
            convex shapes by merging smaller features.

        Returns
        -------
        List[List[Tuple[float, float]]]
            A list where each element is a list of vertices defining a
            specific convex sub-polygon.
        """
        # 1. 采样获取高质量点集
        refined_points = self.__get_refined_points(mob, n_divisions)
        # 2. 转换成相对于中心的局部坐标（物理引擎需要）
        center = mob.get_center()
        local_points = [(p[0] - center[0], p[1] - center[1]) for p in refined_points]
        if len(local_points) < 3:
            return []
        try:
            convex_hulls = autogeometry.convex_decomposition(local_points, tolerance)
            return convex_hulls
        except Exception as e:
            manim_pymunk_logger.error(
                "Decomposition failed, attempting to downgrade to convex hull. Please check if the SVG path is clockwise: {e}"
            )
            hull = autogeometry.to_convex_hull(local_points, tolerance)
            return [hull]

    @staticmethod
    def _add_shape_filter(
        mob: Mobject,
        group: int = 0,
        categories: int = 4294967295,
        mask: int = 4294967295,
    ):
        """Configures collision filtering for all shapes associated with a Mobject.

        This method defines which objects can collide with each other using Pymunk's
        filtering rules. It uses group IDs to ignore collisions between related
        shapes and bitmasks (categories and masks) for complex layered filtering.

        Parameters
        ----------
        mob
            The Mobject whose shapes will receive the collision filter.
        group
            Shapes in the same non-zero group do not collide. Useful for
            ignoring collisions between parts of the same complex object.
        categories
            A bitmask representing the categories this shape belongs to.
            Default is all categories (32 bits set to 1).
        mask
            A bitmask representing which categories this shape will collide with.
            Default is all categories.
        """
        shape_filter = pymunk.ShapeFilter(group, categories, mask)
        for shape in mob.shapes:
            shape.filter = shape_filter

    @staticmethod
    def get_point_query_info(
        mob: Mobject, point: Tuple[float, float, float] = (0, 0, 0)
    ) -> list:
        query_info_list = []
        for shape in mob.shapes:
            point_query_info = shape.point_query(point[:2])
            query_info_list.append(
                (
                    point_query_info.distance,
                    [*point_query_info.gradient, 0],
                    [*point_query_info.point, 0],
                    point_query_info.shape,
                )
            )
        return query_info_list

    @staticmethod
    def get_line_query(
        mob: Mobject,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        stroke_width: float,
    ) -> list:
        query_info_list = []
        for shape in mob.shapes:
            line_query_info = shape.segment_query(
                start=start[:2], end=end[:2], radius=stroke_width
            )
            query_info_list.append(
                (
                    line_query_info.alpha,
                    [*line_query_info.normal, 0],
                    [*line_query_info.point, 0],
                    line_query_info.shape,
                )
            )
        return query_info_list

    @staticmethod
    def get_shapea_shapeb_info(shape_a: pymunk.Shape, shape_b: pymunk.Shape) -> list:
        contactPointSet = shape_a.shapes_collide(shape_b)
        normal = [*contactPointSet.normal, 0]
        contactPoints = contactPointSet.points
        contact_info = []
        for contact_point in contactPoints:
            contact_info.append(
                (
                    [*contact_point.point_a, 0],
                    [*contact_point.point_b, 0],
                    contact_point.distance,
                )
            )
        return [normal, *contact_info]
