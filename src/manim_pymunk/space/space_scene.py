from manim import *
from manim_pymunk.constraints.constraint import VConstraint
import pymunk
from typing import Tuple
from manim.mobject.mobject import Mobject

from manim_pymunk.space import VSpace

from manim_pymunk.utils.logger_tool import manim_pymunk_logger


class SpaceScene(ZoomedScene):
    """基于 Pymunk 物理引擎的 Manim 基础场景类。

    该场景自动集成了一个物理空间 (VSpace)，用于处理刚体动力学模拟。
    所有加入此场景的物体都可以被赋予物理属性。

    Attributes:
        vspace (VSpace): 场景持有的物理空间管理对象。
    """

    def __init__(self, gravity: Tuple[float, float] = (0, -9.81), **kwargs):
        """初始化物理场景。

        Args:
            renderer: Manim 渲染器实例。
            **kwargs: 传递给 ZoomedScene 的额外参数。
        """
        super().__init__(**kwargs)
        self.vspace = VSpace(gravity=gravity)
        manim_pymunk_logger.debug("SpaceScene initional~")

    def setup(self):
        """场景初始化配置。

        自动将物理空间添加到场景中并启动物理状态更新器 (Updater)。
        """
        self.add(self.vspace)
        self.vspace.init_updater()

    # 配置过滤器
    def add_shapes_filter(
        self,
        *mobs,
        group: int = 0,
        categories: int = 4294967295,
        mask: int = 4294967295,
    ):
        """为指定的物体添加碰撞过滤器。

        Args:
            *mobs: 需要配置过滤器的 Manim 对象。
            group: 碰撞组 ID。同一组的对象不碰撞。
            categories: 类别位掩码。
            mask: 碰撞掩码。
        """
        for mob in mobs:
            self.vspace._add_shape_filter(mob, group, categories, mask)
            
    # --- 语义化快捷接口 ---
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
        """添加静态刚体（如地面、障碍物）"""
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
        """添加动力学刚体（受重力影响）"""
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

    # 添加约束组件
    def add_constraints(self, *mobs: VConstraint):
        """向物理空间添加约束组件（如弹簧、滑轮等）。

        Args:
            *mobs: 包含约束逻辑的物理对象。
        """
        self.add(*mobs)
        for mob in mobs:
            mob.install(space=self.vspace.space)

    # 激活
    def active_body(self, *mobs: Mobject) -> None:
        for mob in mobs:
            # 解决组的问题
            family = mob.family_members_with_points()
            for sub_mob in family:
                if (
                    hasattr(sub_mob, "body")
                    and sub_mob.body.body_type is pymunk.Body.DYNAMIC
                    and sub_mob.body.is_sleeping
                ):
                    sub_mob.body.activate()

    # 休眠
    def sleep_body(self, *mobs: Mobject) -> None:
        for mob in mobs:
            # 解决组的问题
            family = mob.family_members_with_points()
            for sub_mob in family:
                if (
                    hasattr(sub_mob, "body")
                    and sub_mob.body.body_type is pymunk.Body.DYNAMIC
                ):
                    sub_mob.body.sleep()

    # 物理调试图像，当你不清楚约束是否正确时，应当使用它
    def draw_debug_img(self, option: int = None, xlim=(-8, 8), ylim=(-5, 5)) -> None:
        """使用 Matplotlib 弹出物理空间的调试窗口。

        .. note::
           该方法会阻塞当前程序的执行，直到手动关闭弹出的窗口。

        Args:
            option: Pymunk 调试绘制选项。
            xlim: X轴显示范围。
            ylim: Y轴显示范围。
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
            )

        self.vspace.space.debug_draw(draw_options)

        # block=True 会阻塞程序直到你手动关闭窗口
        plt.show(block=True)

    @staticmethod
    def get_body(mob: Mobject) -> pymunk.Body | None:
        """从 Manim 对象中提取绑定的 Pymunk Body 对象。

        Args:
            mob: 目标对象。

        Returns:
            Optional[pymunk.Body]: 绑定的物理主体，若无则抛出异常。

        Raises:
            RuntimeError: 当物体尚未添加到物理空间时抛出。
        """
        if hasattr(mob, "body"):
            return mob.body
        else:
            raise "Please add 'mobject' to the space first!"

    @staticmethod
    def get_shapes(mob: Mobject) -> list[pymunk.Shape] | None:
        """获取mob的shapes列表
        Args:
            mob: Mobject 对象
        """
        if hasattr(mob, "shapes"):
            return mob.shapes
        else:
            raise "Please add 'mobject' to the space first!"
