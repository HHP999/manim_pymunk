"""Pymunk物理引擎与Manim动画库的集成模块。

该模块提供VSpace类，用于管理Pymunk物理空间中的刚体、形状和约束，
并将其与Manim的Mobject视觉对象进行同步更新。

Typical usage example:
    space = VSpace(gravity=(0, -9.81))
    space.init_updater()
    mob = Circle()
    space.set_body_angle_shape(mob, body_type=pymunk.Body.DYNAMIC)
"""

from manim import *
import pymunk
from pymunk import Body, autogeometry
from typing import Callable, Dict, Any
from typing import Tuple
import numpy as np
from manim.constants import RIGHT, UP
from manim.mobject.geometry.arc import Circle
from manim.mobject.geometry.line import Line
from manim.mobject.mobject import Mobject
from manim.mobject.types.vectorized_mobject import VMobject
from manim.utils.bezier import subdivide_bezier
from pymunk.autogeometry import march_soft, convex_decomposition
from manim_pymunk.utils.img_tools import get_normalized_convex_polygons

from manim_pymunk.types import *

# 用于兼容 渲染器
try:
    # For manim < 0.15.0
    from manim.mobject.opengl_compatibility import ConvertToOpenGL
except ModuleNotFoundError:
    # For manim >= 0.15.0
    from manim.mobject.opengl.opengl_compatibility import ConvertToOpenGL


class VSpace(Mobject, metaclass=ConvertToOpenGL):
    """Pymunk物理空间的Manim可视化管理器。
    
    VSpace类封装了Pymunk物理引擎的Space对象，负责管理物理模拟中的
    刚体(Body)、形状(Shape)和约束(Constraint)，并通过updater机制
    将物理模拟结果实时同步到Manim的Mobject视觉对象。
    
    Attributes:
        space (pymunk.Space): 底层Pymunk物理空间对象。
        sub_step (int): 物理模拟的子步数，用于提高模拟精度。
    """

    def __init__(
        self, gravity: Tuple[float, float] = (0, -9.81), sub_step: int = 8, **kwargs
    ):
        """初始化VSpace物理空间。
        
        Args:
            gravity (Tuple[float, float], optional): 重力加速度向量，默认为(0, -9.81)。
            sub_step (int, optional): 每帧的物理子步数，默认为8。用于提高数值模拟稳定性。
            **kwargs: 传递给父类Mobject的其他参数。
        """
        super().__init__(**kwargs)
        self.space = pymunk.Space()
        self.space.gravity = gravity
        self.space.sleep_time_threshold = 5
        self.sub_step: int = sub_step

    # ================================== 初始化 ==================================
    def init_updater(self):
        """初始化物理模拟更新器。
        
        将__step_updater绑定到该Mobject，使其在每一帧都执行
        一步物理模拟计算。
        """
        self.add_updater(self.__step_updater)

    # ================================== 更新器 ==================================
    def __step_updater(self, vspace, dt):
        """执行物理模拟的单帧更新步骤。
        
        将一帧的时间分割成多个子步，分别对物理空间进行step计算，
        以提高数值模拟的稳定性和精度。
        
        Args:
            vspace (VSpace): 物理空间对象本身（self）。
            dt (float): 本帧的时间增量（秒）。
        """
        sub_dt = dt / self.sub_step
        for _ in range(self.sub_step):
            vspace.space.step(sub_dt)

    def __simulate_updater(self, mob: Mobject):
        """同步Mobject与其物理体的位置和旋转角度。
        
        从刚体(Body)读取最新的位置和角度信息，更新对应Mobject
        的视觉位置，确保动画对象与物理模拟保持同步。
        
        Args:
            mob (Mobject): 需要同步的Manim视觉对象。
        """
        x, y = mob.body.position
        mob.move_to(x * RIGHT + y * UP)
        mob.rotate(mob.body.angle - mob.angle)
        mob.angle = mob.body.angle

    # =============================== space 相关 ==================================
    def remove_body_shapes_constraints(self, *items):
        """从物理空间中移除刚体、形状或约束。
        
        Args:
            *items: 要移除的Pymunk对象（Body、Shape或Constraint）。
        """
        self.space.remove(*items)

    def _add_body2space(self, mob: Mobject) -> None:
        """将Mobject的刚体和形状添加到物理空间。
        
        如果刚体是静态刚体，仅添加形状；否则同时添加刚体和形状。
        并为Mobject绑定模拟更新器以保持视觉同步。
        
        Args:
            mob (Mobject): 包含body和shapes属性的Mobject对象。
        """
        if mob.body is self.space.static_body:
            # 不需要添加updaters
            self.space.add(*mob.shapes)
        else:
            self.space.add(mob.body)
            self.space.add(*mob.shapes)
        # 使用更新器绑定mob位置
        mob.add_updater(self.__simulate_updater)
        # 激活
        mob.body.activate()

    def __set_body(self, mob: VMobject, body_type: int) -> None:
        """为Mobject创建并配置Pymunk刚体。
        
        根据指定的刚体类型（DYNAMIC、KINEMATIC或STATIC）创建对应的
        Pymunk Body对象，并将Mobject的当前位置设置为刚体的初始位置。
        
        Args:
            mob (VMobject): 要配置的Mobject对象。
            body_type (int): 刚体类型，可选值为pymunk.Body.DYNAMIC、
                KINEMATIC或STATIC。
        """
        if not hasattr(mob, "body"):
            mob.set(body=None)
        # 为动态物体提供默认的质量和惯性矩，否则会报错
        if body_type == pymunk.Body.DYNAMIC:
            mob.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        elif body_type == pymunk.Body.KINEMATIC:
            mob.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        else:
            mob.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        # 先有body后有pos
        mob.body.position = mob.get_x(), mob.get_y()

    def __set_angle(self, mob: VMobject) -> None:
        """初始化Mobject的旋转角度属性。
        
        为Mobject添加angle属性（如果不存在），用于跟踪其旋转状态。
        
        Args:
            mob (VMobject): 要配置的Mobject对象。
        """
        if not hasattr(mob, "angle"):
            mob.set(angle=0)

    def set_body_angle_shape(
        self, mob: Mobject, body_type=pymunk.Body.DYNAMIC, is_solid: bool = True
    ) -> None:
        """为Mobject完整配置物理属性：刚体、角度和形状。
        
        这是一个综合方法，依次调用__set_body、__set_angle、__set_shape
        和_add_body2space，完成Mobject的完整物理配置。
        
        Args:
            mob (Mobject): 要配置的Mobject对象。
            body_type (int, optional): 刚体类型，默认为pymunk.Body.DYNAMIC。
            is_solid (bool, optional): 是否使用实心形状，默认为True。
                若为False，则使用空心形状（仅轮廓碰撞）。
        """
        self.__set_body(mob, body_type)
        self.__set_angle(mob)
        self.__set_shape(mob, is_solid)
        self._add_body2space(mob)

    @staticmethod
    def _set_collision_type(mob: Mobject, collision_type: int):
        """设置Mobject所有形状的碰撞类型。
        
        Args:
            mob (Mobject): 包含shapes属性的Mobject对象。
            collision_type (int): 碰撞类型ID，用于碰撞分组和过滤。
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
        """注册通配符碰撞处理器。
        
        为指定碰撞类型与任何其他类型的碰撞事件注册回调函数。
        这在需要处理某一对象与所有其他对象的碰撞时很有用。
        
        Args:
            collision_type_a (int): 触发碰撞处理的碰撞类型。
            begin (Callable, optional): 碰撞开始时调用的回调函数。
                必须返回True以允许产生物理效果。
            pre_solve (Callable, optional): 碰撞求解前调用的回调函数。
                必须返回True以允许产生物理效果。
            post_solve (Callable, optional): 碰撞求解后调用的回调函数。
            separate (Callable, optional): 碰撞分离时调用的回调函数。
            data (Dict[Any, Any], optional): 传递给回调函数的自定义数据字典。
        
        Returns:
            pymunk.CollisionHandler: 注册的碰撞处理器对象。
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
        """注册两个碰撞类型之间的碰撞处理器。
        
        为两个特定碰撞类型之间的碰撞事件注册回调函数。
        
        Args:
            collision_type_a (int): 第一个碰撞类型。
            collision_type_b (int): 第二个碰撞类型。
            begin (Callable, optional): 碰撞开始时调用的回调函数。
                必须返回True以允许产生物理效果。
            pre_solve (Callable, optional): 碰撞求解前调用的回调函数。
                必须返回True以允许产生物理效果。
            post_solve (Callable, optional): 碰撞求解后调用的回调函数。
            separate (Callable, optional): 碰撞分离时调用的回调函数。
            data (Dict[Any, Any], optional): 传递给回调函数的自定义数据字典。
        
        Returns:
            pymunk.CollisionHandler: 注册的碰撞处理器对象。
        """
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

    # =============================== body 相关 ==================================
    @staticmethod
    def _set_body_config(mob, body_config: BodyConfig):
        """根据BodyConfig对象配置Mobject的刚体属性。
        
        应用包括质量、转动惯量、位置、角度、速度、角速度和受力
        等所有物理属性。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            body_config (BodyConfig): 包含刚体配置参数的对象。
        """
        body = mob.body

        # 1. 设置物理基本属性
        body.body_type = body_config.body_type

        if body_config.mass > 0:
            body.mass = body_config.mass
        if body_config.moment > 0:
            body.moment = body_config.moment

        body.center_of_gravity = body_config.center_of_gravity

        # 2. 设置空间状态 (处理 None 的逻辑)
        if body_config.position is not None:
            body.position = body_config.position
        else:
            pos = mob.get_center()
            body.position = (pos[0], pos[1])

        body.angle = body_config.angle

        # 3. 设置运动状态
        body.velocity = body_config.velocity
        body.angular_velocity = body_config.angular_velocity

        # 4. 设置受力
        body.force = body_config.force
        body.torque = body_config.torque

    @staticmethod
    def apply_force_at_local_point(
        mob: Mobject, force: tuple[float, float], point=[0, 0, 0]
    ) -> None:
        """在刚体局部坐标系中的指定点施加力。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            force (tuple[float, float]): 力的向量，格式为(fx, fy)。
            point (list, optional): 施加力的点，局部坐标，默认为刚体中心[0, 0, 0]。
        """
        mob.body.apply_force_at_local_point(force=force, point=point[:2])

    @staticmethod
    def apply_force_at_world_point(
        mob: Mobject, force: tuple[float, float], point=[0, 0, 0]
    ) -> None:
        """在世界坐标系中的指定点施加力。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            force (tuple[float, float]): 力的向量，格式为(fx, fy)。
            point (list, optional): 施加力的点，世界坐标，默认为原点[0, 0, 0]。
        """
        mob.body.apply_force_at_world_point(force=force, point=point[:2])

    @staticmethod
    def apply_impulse_at_local_point(
        mob: Mobject, impulse: tuple[float, float], point=[0, 0, 0]
    ) -> None:
        """在刚体局部坐标系中的指定点施加脉冲（瞬间冲量）。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            impulse (tuple[float, float]): 脉冲向量，格式为(ix, iy)。
            point (list, optional): 施加脉冲的点，局部坐标，默认为刚体中心[0, 0, 0]。
        """
        mob.body.apply_impulse_at_local_point(impulse=impulse, point=point[:2])

    @staticmethod
    def apply_impulse_at_world_point(
        mob: Mobject, impulse: tuple[float, float], point=[0, 0, 0]
    ) -> None:
        """在世界坐标系中的指定点施加脉冲（瞬间冲量）。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            impulse (tuple[float, float]): 脉冲向量，格式为(ix, iy)。
            point (list, optional): 施加脉冲的点，世界坐标，默认为原点[0, 0, 0]。
        """
        mob.body.apply_impulse_at_world_point(impulse=impulse, point=point[:2])

    @staticmethod
    def local_to_world(mob, point=[0, 0, 0]):
        """将局部坐标系中的点转换为世界坐标系中的点。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            point (list, optional): 局部坐标点，默认为[0, 0, 0]。
        
        Returns:
            list: 对应的世界坐标点[x, y, 0]。
        """
        world_pos = mob.body.local_to_world(point[:2])
        return [*world_pos, 0]

    @staticmethod
    def world_to_local(mob, point=[0, 0, 0]):
        """将世界坐标系中的点转换为局部坐标系中的点。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            point (list, optional): 世界坐标点，默认为[0, 0, 0]。
        
        Returns:
            list: 对应的局部坐标点[x, y, 0]。
        """
        local_pos = mob.body.world_to_local(point[:2])
        return [*local_pos, 0]

    @staticmethod
    def set_position_func(mob, callback: Callable[[Body, float], None] = None):
        """为刚体设置自定义位置更新回调函数。
        
        该回调函数在每个物理仿真步骤中被调用，可用于实现自定义
        的位置更新逻辑。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            callback (Callable, optional): 回调函数，签名为
                def callback(body: Body, dt: float): ...
        """
        if callback:
            mob.body.position_func = callback

    @staticmethod
    def set_velocity_func(
        mob, callback: Callable[[Body, tuple[float, float], float, float], None] = None
    ):
        """为刚体设置自定义速度更新回调函数。
        
        该回调函数在每个物理仿真步骤中被调用，可用于实现自定义
        的速度更新逻辑（如阻尼、空气阻力等）。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            callback (Callable, optional): 回调函数，签名为
                def callback(body: Body, gravity: tuple, damping: float, dt: float): ...
        """
        if callback:
            mob.body.velocity_func = callback

    @staticmethod
    def velocity_at_local_point(mob, point=[0, 0, 0]):
        """获取刚体局部坐标系中指定点的绝对速度。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            point (list, optional): 局部坐标点，默认为[0, 0, 0]。
        
        Returns:
            list: 该点的速度向量[vx, vy, 0]。
        """
        velocity = mob.body.velocity_at_local_point(point[:2])
        return [*velocity, 0]

    @staticmethod
    def velocity_at_world_point(mob, point=[0, 0, 0]):
        """获取刚体世界坐标系中指定点的绝对速度。
        
        Args:
            mob (Mobject): 包含body属性的Mobject对象。
            point (list, optional): 世界坐标点，默认为[0, 0, 0]。
        
        Returns:
            list: 该点的速度向量[vx, vy, 0]。
        """
        velocity = mob.body.velocity_at_world_point(point[:2])
        return [*velocity, 0]

    # =============================== shape 相关 ==================================
    def __set_shape(self, mob: Mobject, is_solid: bool = True) -> None:
        """根据Mobject的几何形状自动生成对应的Pymunk碰撞形状。
        
        支持多种Mobject类型：圆形、直线、多边形、图片等。
        对于复杂的非凸形状，自动进行凸分解。
        
        Args:
            mob (Mobject): 要生成碰撞形状的Mobject对象。
            is_solid (bool, optional): 是否创建实心形状，默认为True。
                若为False，则创建空心形状（仅轮廓）。
        """
        if not hasattr(mob, "shapes"):
            mob.set(shapes=[])

        if isinstance(mob, ImageMobject):
            # 图片
            self.get_img_shape(mob)
        elif is_solid:
            # 实心
            self.get_solid_shape(mob)
        else:
            # 空心
            self.get_hollow_shape(mob)

        # 配置属性
        for shape in mob.shapes:
            shape.density = 1
            shape.elasticity = 0
            shape.friction = 0

    def get_solid_shape(self, mob: VMobject) -> None:
        """为实心Mobject生成Pymunk碰撞形状。
        
        根据Mobject的类型（Circle、Line、Polygon等）创建相应的
        Pymunk形状。对于复杂的非凸多边形（如Star），进行自动凸分解。
        
        Args:
            mob (VMobject): 要生成碰撞形状的向量图形对象。
        """
        stroke_width = (mob.stroke_width / 100) * (
            config.frame_height / config.frame_width
        )
        # 1. 圆形处理
        if isinstance(mob, Circle):
            mob.shapes = [
                pymunk.Circle(body=mob.body, radius=mob.radius + stroke_width / 2)
            ]

        # 2. 直线处理
        elif isinstance(mob, Line):
            center_x, center_y = mob.get_center()[:2]
            start = mob.get_start()
            end = mob.get_end()

            # 计算局部偏移
            local_a = (start[0] - center_x, start[1] - center_y)
            local_b = (end[0] - center_x, end[1] - center_y)

            mob.shapes = [pymunk.Segment(mob.body, local_a, local_b, stroke_width / 2)]

        # 3. 闭合路径处理 (包括 Polygram, Star, RegularPolygon, 以及复杂的 VMobject)
        else:
            local_points = self.get_refined_points(mob, n_divisions=8)

            if len(local_points) < 3:
                return

            # 使用现成工具判断是否为凸
            hull = autogeometry.to_convex_hull(local_points, 0.001)
            is_convex = len(hull) == len(local_points)

            if is_convex:
                # 凸多边形：直接生成单个 Shape
                mob.shapes.append(
                    pymunk.Poly(mob.body, local_points, radius=stroke_width / 2)
                )
            else:
                # 凹多边形（如 Star）：调用分解函数
                convex_hulls = self.concave2convex_refined(
                    mob, n_divisions=8, tolerance=0.01
                )
                for hull_verts in convex_hulls:
                    mob.shapes.append(
                        pymunk.Poly(mob.body, hull_verts, radius=stroke_width / 2)
                    )

    def get_hollow_shape(self, mob: VMobject, n_divisions: int = 4) -> None:
        """为空心Mobject生成Pymunk碰撞形状（仅轮廓）。
        
        使用多个Segment（线段）形状围绕Mobject轮廓创建碰撞边界，
        适用于需要空心碰撞效果的场景。
        
        Args:
            mob (VMobject): 要生成碰撞形状的向量图形对象。
            n_divisions (int, optional): 贝塞尔曲线细分级数，默认为4。
        """
        stroke_width = (mob.stroke_width / 100) * (
            config.frame_height / config.frame_width
        )
        refined_points = self.get_refined_points(mob)
        # 转换成相对于中心的局部坐标（物理引擎需要）
        center = mob.get_center()
        refined_points = [(p[0] - center[0], p[1] - center[1]) for p in refined_points]

        n_pts = len(refined_points)
        if n_pts < 2:
            return

        for j in range(n_pts):
            p1 = refined_points[j]
            # 将末尾点连回起始点
            p2 = refined_points[(j + 1) % n_pts]

            # 过滤：如果两点完全重合，Pymunk 会报错
            if np.allclose(p1, p2, atol=1e-4):
                continue

            seg = pymunk.Segment(
                mob.body, (p1[0], p1[1]), (p2[0], p2[1]), radius=stroke_width / 2
            )
            mob.shapes.append(seg)

    def get_img_shape(self, mob: ImageMobject) -> None:
        """为图片生成Pymunk碰撞形状。
        
        从图片像素数据中提取凸多边形，用作碰撞形状。
        如果无法提取有效多边形，则使用矩形边界。
        
        Args:
            mob (ImageMobject): 要生成碰撞形状的图片对象。
        """
        pixel_array = mob.pixel_array
        manim_w, manim_h = mob.width, mob.height
        polygons = get_normalized_convex_polygons(
            pixel_array,
            base_width=512.0,
            target_cell_size=4,
            frame_w=manim_w,
            frame_h=manim_h,
        )
        if polygons:
            # 根据 polygons 生成多边形
            for poly_verts in polygons:
                mob.shapes.append(pymunk.Poly(mob.body, poly_verts, radius=0.1))
        else:
            mob.shapes = [
                pymunk.Poly.create_box(mob.body, size=(manim_w, manim_h), radius=0.1)
            ]

    @staticmethod
    def get_refined_points(mob: VMobject, n_divisions: int = 4):
        """提取Mobject的细分采样点，用于生成精细的碰撞形状。
        
        对贝塞尔曲线进行细分，获取高分辨率的点集。
        自动去除浮点数误差导致的重复点。
        
        Args:
            mob (VMobject): 输入的向量图形对象。
            n_divisions (int, optional): 贝塞尔细分级数，默认为4。
                级数越大，采样点越密集，曲线越平滑。
        
        Returns:
            list: 细分后的采样点列表，每个点为(x, y)元组。
        """
        all_points = []
        for submob in mob.family_members_with_points():
            pts = submob.points
            if len(pts) == 0:
                continue

            # 贝塞尔细分
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

    def concave2convex_refined(
        self, mob: VMobject, n_divisions: int = 8, tolerance: float = 0.1
    ):
        """将非凸多边形分解为多个凸多边形。
        
        对于Star、复杂多边形等非凸形状，使用Pymunk的凸分解算法
        将其分解为若干凸多边形，便于物理碰撞计算。
        
        Args:
            mob (VMobject): 要分解的向量图形对象。
            n_divisions (int, optional): 贝塞尔采样细分级数，默认为8。
            tolerance (float, optional): 凸分解容差，默认为0.1。
        
        Returns:
            list: 凸多边形顶点列表的列表，每个子列表代表一个凸多边形。
        """
        # 1. 采样获取高质量点集
        refined_points = self.get_refined_points(mob, n_divisions)
        # 2. 转换成相对于中心的局部坐标（物理引擎需要）
        center = mob.get_center()
        local_points = [(p[0] - center[0], p[1] - center[1]) for p in refined_points]
        if len(local_points) < 3:
            return []
        try:
            # 3. 分解
            convex_hulls = autogeometry.convex_decomposition(local_points, tolerance)
            return convex_hulls
        except Exception as e:
            print(f"分解失败，尝试降级为凸包: {e}")
            hull = autogeometry.to_convex_hull(local_points, tolerance)
            return [hull]

    @staticmethod
    def _set_shape_config(mob, shape_config: ShapeConfig):
        """根据ShapeConfig对象配置Mobject所有形状的属性。
        
        应用包括弹性、摩擦力、质量、碰撞类型等所有形状相关的物理属性。
        
        Args:
            mob (Mobject): 包含shapes属性的Mobject对象。
            shape_config (ShapeConfig): 包含形状配置参数的对象。
        """
        # 假设 mob.shape 已经在初始化时根据几何形状（如 Circle, Poly）创建完成
        for shape in mob.shapes:
            # 1. 材质属性
            shape.elasticity = shape_config.elasticity
            shape.friction = shape_config.friction

            # 2. 质量分配逻辑
            if shape_config.mass is not None:
                shape.mass = shape_config.mass
            else:
                shape.density = shape_config.density

            # 3. 碰撞过滤与识别
            shape.collision_type = shape_config.collision_type

            # 4. 特殊功能
            shape.sensor = shape_config.sensor
            shape.surface_velocity = shape_config.surface_velocity

    @staticmethod
    def _add_shape_filter(
        mob, group: int = 0, categories: int = 4294967295, mask: int = 4294967295
    ):
        """为Mobject的所有形状配置碰撞过滤器。
        
        通过设置碰撞分组和掩码，控制哪些形状之间会发生碰撞检测。
        
        Args:
            mob (Mobject): 包含shapes属性的Mobject对象。
            group (int, optional): 碰撞分组ID，默认为0。
                同组的形状之间的碰撞可根据规则被忽略。
            categories (int, optional): 形状所属的碰撞类别位掩码，默认为4294967295。
            mask (int, optional): 形状会检测的碰撞类别位掩码，默认为4294967295。
        """
        shape_filter = pymunk.ShapeFilter(group, categories, mask)
        shapes = mob.shapes
        for shape in shapes:
            shape.filter = shape_filter

    @staticmethod
    def get_point_query_info(mob, point=[0, 0, 0]):
        """查询世界坐标中一个点与Mobject形状的碰撞信息。
        
        返回点到每个形状的最近距离、法向量和最近点等信息。
        负距离表示点在形状内部。
        
        Args:
            mob (Mobject): 包含shapes属性的Mobject对象。
            point (list, optional): 世界坐标中的查询点，默认为[0, 0, 0]。
        
        Returns:
            list: 包含(distance, gradient, point, shape)元组的列表。
                distance: 有符号距离，负值表示点在形状内。
                gradient: 有符号距离函数的梯度向量[gx, gy, 0]。
                point: 形状上最近的点[px, py, 0]。
                shape: 最近的形状对象。
        """
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
        mob,
        start: list[float, float, float],
        end: list[float, float, float],
        stroke_width: float,
    ):
        """查询一条线段与Mobject形状的碰撞信息。
        
        返回线段与每个形状的交点、法向量和碰撞位置等信息。
        
        Args:
            mob (Mobject): 包含shapes属性的Mobject对象。
            start (list[float, float, float]): 线段起点世界坐标。
            end (list[float, float, float]): 线段终点世界坐标。
            stroke_width (float): 线段的有效宽度（半径）。
        
        Returns:
            list: 包含(alpha, normal, point, shape)元组的列表。
                alpha: 碰撞点在线段上的相对位置（0.0-1.0）。
                normal: 碰撞点处的法线向量[nx, ny, 0]。
                point: 碰撞点的世界坐标[px, py, 0]。
                shape: 被碰撞的形状对象。
        """
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
    def get_shapea_shapeb_info(shape_a, shape_b):
        """查询两个形状之间的碰撞信息。
        
        返回两个形状的碰撞法线和所有接触点。
        负距离表示两个形状相互穿透。
        
        Args:
            shape_a (pymunk.Shape): 第一个Pymunk形状对象。
            shape_b (pymunk.Shape): 第二个Pymunk形状对象。
        
        Returns:
            tuple: 包含碰撞法线和接触点信息的元组。
                第一个元素: 碰撞法线[nx, ny, 0]。
                后续元素: 每个接触点的(point_a, point_b, distance)信息。
                    point_a: shape_a 上的世界碰撞点[px, py, 0]。
                    point_b: shape_b 上的世界碰撞点[px, py, 0]。
                    distance: 穿透距离，负值表示碰撞。
        """
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
        return (normal, *contact_info)
