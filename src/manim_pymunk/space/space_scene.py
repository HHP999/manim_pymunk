from manim import *
import pymunk


from typing import Tuple
from manim.mobject.mobject import Mobject
from manim.mobject.types.vectorized_mobject import VMobject

from manim_pymunk.types import *
from manim_pymunk.space import VSpace


class SpaceScene(ZoomedScene):
    """基于 Pymunk 物理引擎的 Manim 基础场景类。

    该场景自动集成了一个物理空间 (VSpace)，用于处理刚体动力学模拟。
    所有加入此场景的物体都可以被赋予物理属性。

    Attributes:
        GRAVITY (Tuple[float, float]): 全局重力向量，默认为 (0, -9.81)。
        vspace (VSpace): 场景持有的物理空间管理对象。
    """

    GRAVITY: Tuple[float, float] = 0, -9.81

    def __init__(self, renderer=None, **kwargs):
        """初始化物理场景。

        Args:
            renderer: Manim 渲染器实例。
            **kwargs: 传递给 ZoomedScene 的额外参数。
        """
        self.vspace = VSpace(gravity=self.GRAVITY)
        super().__init__(renderer=renderer, **kwargs)

    def setup(self):
        """场景初始化配置。

        自动将物理空间添加到场景中并启动物理状态更新器 (Updater)。
        """
        self.add(self.vspace)
        self.vspace.init_updater()

    def get_space_tatic_body(self):
        """获取物理空间的静态主体对应的 Manim 对象。

        Returns:
            VMobject: 绑定了 Pymunk 静态刚体的对象。
        """
        mob = VMobject()
        mob.set(body=self.vspace.space.static_body)
        return mob

    # 配置过滤器
    def add_shape_filter(
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

    # 把pymunk的body,shapes加入 mob
    def add_static_body(self, *mobs: Mobject, family_members=False):
        """将物体作为静态刚体 (Static Body) 添加到场景。

        静态物体通常用于地面、墙壁等不动的障碍物。

        Args:
            *mobs: 需要添加的 Manim 对象。
            family_members: 是否包含子物件的所有成员。
        """
        self.add(*mobs)
        for mob in mobs:
            if family_members:
                fimily = mob.family_members_with_points()
                for sub_mob in fimily:
                    self.vspace.set_body_angle_shape(
                        sub_mob, body_type=pymunk.Body.STATIC
                    )
            else:
                self.vspace.set_body_angle_shape(mob, body_type=pymunk.Body.STATIC)

    def add_dynamic_body(
        self,
        *mobs: Mobject,
        family_members=False,
        is_solid: bool = True,
    ):
        """将物体作为动力学刚体 (Dynamic Body) 添加到场景。

        动力学物体受重力、摩擦力和碰撞力的影响。

        Args:
            *mobs: 需要添加的对象。
            family_members: 是否处理子物件成员。
            is_solid: 是否开启实心碰撞检测。
        """
        self.add(*mobs)
        for mob in mobs:
            if family_members:
                fimily = mob.family_members_with_points()
                for sub_mob in fimily:
                    self.vspace.set_body_angle_shape(
                        sub_mob, body_type=pymunk.Body.DYNAMIC, is_solid=is_solid
                    )
            else:
                self.vspace.set_body_angle_shape(
                    mob, body_type=pymunk.Body.DYNAMIC, is_solid=is_solid
                )

    def add_kinematic_body(
        self,
        *mobs: Mobject,
        family_members=False,
    ):
        self.add(*mobs)
        for mob in mobs:
            if family_members:
                fimily = mob.family_members_with_points()
                for sub_mob in fimily:
                    self.vspace.set_body_angle_shape(
                        sub_mob, body_type=pymunk.Body.KINEMATIC
                    )
            else:
                self.vspace.set_body_angle_shape(mob, body_type=pymunk.Body.KINEMATIC)

    # 添加约束组件
    def add_constraints_body(self, *mobs: Mobject):
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
            fimily = mob.family_members_with_points()
            for sub_mob in fimily:
                if (
                    hasattr(sub_mob, "body")
                    and sub_mob.body.body_type is pymunk.Body.DYNAMIC
                    and sub_mob.body.is_sleeping
                ):
                    sub_mob.body.activate()

    # 休眠
    def sleep_body(self, *mobs: Mobject) -> None:
        for mob in mobs:
            fimily = mob.family_members_with_points()
            for sub_mob in fimily:
                if (
                    hasattr(sub_mob, "body")
                    and sub_mob.body.body_type is pymunk.Body.DYNAMIC
                ):
                    sub_mob.body.sleep()

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

        fig, ax = plt.subplots(figsize=(6, 6))
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
