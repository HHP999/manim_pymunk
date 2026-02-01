from manim import *
import pymunk
from pymunk import autogeometry
from typing import Callable, Dict, Any
from typing import Tuple
import numpy as np
from manim.constants import RIGHT, UP
from manim.mobject.geometry.arc import Circle
from manim.mobject.geometry.line import Line
from manim.mobject.mobject import Mobject
from manim.mobject.types.vectorized_mobject import VMobject
from manim.utils.bezier import subdivide_bezier

from manim_pymunk.types import *

# 用于兼容 渲染器
try:
    # For manim < 0.15.0
    from manim.mobject.opengl_compatibility import ConvertToOpenGL
except ModuleNotFoundError:
    # For manim >= 0.15.0
    from manim.mobject.opengl.opengl_compatibility import ConvertToOpenGL


# 主要目的是创建空 Mobject，使用它的更新器
class VSpace(Mobject, metaclass=ConvertToOpenGL):
    def __init__(
        self, gravity: Tuple[float, float] = (0, -9.81), sub_step: int = 8, **kwargs
    ):
        super().__init__(**kwargs)
        self.space = pymunk.Space()
        self.space.gravity = gravity
        self.space.sleep_time_threshold = 5
        self.sub_step: int = sub_step

    # 添加更新器
    def __step_updater(self, vspace, dt):
        """定义为类的方法"""
        sub_dt = dt / self.sub_step
        for _ in range(self.sub_step):
            vspace.space.step(sub_dt)

    def init_updater(self):
        # 注意这里绑定的是 self._step_updater
        self.add_updater(self.__step_updater)

    # 可视化更新
    def __simulate_updater(self, mob: Mobject):
        x, y = mob.body.position
        mob.move_to(x * RIGHT + y * UP)
        mob.rotate(mob.body.angle - mob.angle)
        mob.angle = mob.body.angle

    # 将 刚体 body 加入模拟空间
    def __add_body2space(self, mob: Mobject):
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

    # 配置 body
    def __set_body(self, mob: VMobject, body_type: int) -> None:
        if not hasattr(mob, "body"):
            mob.set(body=None)
        # 为动态物体提供默认的质量和惯性矩，否则会报错
        if body_type == pymunk.Body.DYNAMIC:
            # mass = 1.0
            # moment = pymunk.moment_for_circle(mass, 1, 1)  # 占位
            mob.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        elif body_type == pymunk.Body.KINEMATIC:
            mob.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        else:
            mob.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        # 先有body后有pos
        mob.body.position = mob.get_x(), mob.get_y()

    # 添加shapes
    def __set_shape(self, mob: VMobject, is_solid: bool = True) -> None:
        if not hasattr(mob, "shapes"):
            mob.set(shapes=[])
        # 圆形，多边形，线条
        if is_solid:
            self.get_solid_shape(mob)
        else:
            self.get_hollow_shape(mob)

    # 获取 VMobject 初始角度
    def __set_angle(self, mob: VMobject) -> None:
        if not hasattr(mob, "angle"):
            mob.set(angle=0)
        # anchors = mob.get_anchors()
        # if len(anchors) >= 2:
        #     # 计算第一个特征向量
        #     vec_0  = anchors[0] - anchors[1]
        #     vec_1  = [1, 0, 0]
        #     mob.angle = angle_between_vectors(vec_0, vec_1)
        # mob.body.angle = mob.angle

    def get_solid_shape(self, mob: VMobject) -> None:
        # 1. 圆形处理
        if isinstance(mob, Circle):
            mob.shapes = [pymunk.Circle(body=mob.body, radius=mob.radius)]

        # 2. 直线处理
        elif isinstance(mob, Line):
            center_x, center_y = mob.get_center()[:2]
            start = mob.get_start()  # 或者你自定义的起始点坐标
            end = mob.get_end()

            # 计算局部偏移
            local_a = (start[0] - center_x, start[1] - center_y)
            local_b = (end[0] - center_x, end[1] - center_y)

            mob.shapes = [pymunk.Segment(mob.body, local_a, local_b, 0.1)]

        # 3. 闭合路径处理 (包括 Polygram, Star, RegularPolygon, 以及复杂的 VMobject)
        else:
            # 统一提取高精度采样点
            # n_divisions=4 足够应付大多数多边形，若是曲线文字建议设为 8
            local_points = self.get_refined_points(mob, n_divisions=8)

            if len(local_points) < 3:
                return

            # --- 关键判断：使用现成工具判断是否为凸 ---
            # 如果凸包的点数等于原始采样点数，说明它已经是凸的了
            hull = autogeometry.to_convex_hull(local_points, 0.001)
            is_convex = len(hull) == len(local_points)

            if is_convex:
                # 凸多边形：直接生成单个 Shape
                mob.shapes.append(pymunk.Poly(mob.body, local_points))
            else:
                # 凹多边形（如 Star）：调用分解函数
                # 注意：分解函数内部也应该是基于 local_points 的
                convex_hulls = self.concave2convex_refined(
                    mob, n_divisions=8, tolerance=0.01
                )
                for hull_verts in convex_hulls:
                    mob.shapes.append(pymunk.Poly(mob.body, hull_verts))

        # 4. 配置属性
        for shape in mob.shapes:
            shape.density = 1
            shape.elasticity = 0.8
            shape.friction = 0.8

    # 绘制空心形状, 使用  Segment 圈
    def get_hollow_shape(self, mob: VMobject, n_divisions: int = 4) -> None:
        refined_points = self.get_refined_points(mob)
        # 2. 转换成相对于中心的局部坐标（物理引擎需要）
        center = mob.get_center()
        refined_points = [(p[0] - center[0], p[1] - center[1]) for p in refined_points]

        n_pts = len(refined_points)
        if n_pts < 2:
            return

        # 增加物理厚度：0.5 以上可以有效防止高速下的“穿墙”
        # 即使视觉上你的线很细，物理上的这根“管子”也要够粗
        physical_thickness = 0.02

        # 使用范围 n_pts 确保处理到每一个点
        for j in range(n_pts):
            p1 = refined_points[j]
            # 关键：使用 (j + 1) % n_pts 将末尾点连回起始点
            p2 = refined_points[(j + 1) % n_pts]

            # 过滤：如果两点完全重合（由于采样精度），Pymunk 会报错
            if np.allclose(p1, p2, atol=1e-4):
                continue

            seg = pymunk.Segment(
                mob.body, (p1[0], p1[1]), (p2[0], p2[1]), physical_thickness
            )

            # 配置物理属性
            seg.density = 1
            seg.elasticity = 0.8
            seg.friction = 0.8
            mob.shapes.append(seg)

    # 曲线细分
    @staticmethod
    def get_refined_points(mob: VMobject, n_divisions: int = 4):
        """提取细分后的所有采样点"""
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
                # n_divisions 越大，曲线越平滑，点越多
                sub_pts = subdivide_bezier(bezier_segment, n_divisions)
                all_points.extend(sub_pts)

        # 转为 2D 坐标并清洗重复点
        # 使用 np.round 辅助去重，防止浮点数微小误差导致的分解失败
        unique_points = []
        for p in all_points:
            p_2d = (float(p[0]), float(p[1]))
            if not unique_points or not np.allclose(p_2d, unique_points[-1], atol=1e-3):
                unique_points.append(p_2d)

        return unique_points

    def concave2convex_refined(
        self, mob: VMobject, n_divisions: int = 8, tolerance: float = 0.1
    ):
        """基于细分点的凸分解"""
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

    def set_body_angle_shape(
        self, mob: Mobject, body_type=pymunk.Body.DYNAMIC, is_solid: bool = True
    ) -> None:
        self.__set_body(mob, body_type)
        if body_type == pymunk.Body.STATIC:
            self.__set_shape(mob, is_solid)
            # mob.body.position = 0, 0
            self.__add_body2space(mob)
            mob.clear_updaters()

        else:
            self.__set_angle(mob)
            self.__set_shape(mob, is_solid)
            self.__add_body2space(mob)
            # # 配置 body 属性
            # self.__set_body_config(mob, body_config)
            # # 配置 shape 属性
            # self.__set_shape_config(mob, shape_config)

    # 属性配置
    @staticmethod
    def _set_body_config(mob, body_config: BodyConfig):
        pass

    @staticmethod
    def _set_shape_config(mob, shape_config: ShapeConfig):
        pass

    @staticmethod
    def _add_shape_filter(
        mob, group: int = 0, categories: int = 4294967295, mask: int = 4294967295
    ):
        shape_filter = pymunk.ShapeFilter(group, categories, mask)
        shapes = mob.shapes
        for shape in shapes:
            shape.filter = shape_filter

    # 碰撞类型配置
    def _set_collision_type(mob: Mobject, collision_type: int):
        for shape in mob.shapes:
            shape.collision_type = collision_type

    # 碰撞检测
    def _collision_detection(
        self,
        collision_type_a: int,
        collision_type_b: int,
        begin: Callable[[pymunk.Arbiter, pymunk.Space, Dict], bool] = None,
        pre_solve: Callable[[pymunk.Arbiter, pymunk.Space, Dict], bool] = None,
        post_solve: Callable[[pymunk.Arbiter, pymunk.Space, Dict], None] = None,
        separate: Callable[[pymunk.Arbiter, pymunk.Space, Dict], None] = None,
        data: Dict[Any, Any] = None,
    ):
        # 1. 创建处理器
        handler = self.space.add_collision_handler(collision_type_a, collision_type_b)

        # 2. 绑定回调 (注意: begin 和 pre_solve 必须返回 True 才能产生物理效果)
        if begin:
            handler.begin = begin
        if pre_solve:
            handler.pre_solve = pre_solve
        if post_solve:
            handler.post_solve = post_solve
        if separate:
            handler.separate = separate

        # 3. 注入数据
        if data:
            handler.data.update(data)

        return handler
