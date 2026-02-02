from manim import *
import pymunk
import matplotlib.pyplot as plt
import pymunk.matplotlib_util

from typing import Tuple
from manim.mobject.mobject import Mobject
from manim.mobject.types.vectorized_mobject import VMobject

from manim_pymunk.types import *
from manim_pymunk.space import VSpace

class SpaceScene(ZoomedScene):
    GRAVITY: Tuple[float, float] = 0, -9.81

    def __init__(self, renderer=None, **kwargs):
        """A basis scene for all of rigid mechanics. The gravity vector
        can be adjusted with ``self.GRAVITY``.
        """
        self.vspace = VSpace(gravity=self.GRAVITY)
        super().__init__(renderer=renderer, **kwargs)

    def setup(self):
        """初始化，添加更新器"""
        self.add(self.vspace)
        self.vspace.init_updater()

    def get_space_tatic_body(self):
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
        for mob in mobs:
            self.vspace._add_shape_filter(mob, group, categories, mask)

    # 把pymunk的body,shapes加入 mob
    def add_static_body(self, *mobs: Mobject, family_members=False):
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
        elasticity: float = 0.8,
        density: float = 1,  # 使用密度自动计算质量
        friction: float = 0.8,
        family_members=False,
        is_solid: bool = True,
    ):
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
        elasticity: float = 0.8,
        density: float = 1,  # 使用密度自动计算质量
        friction: float = 0.8,
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
        if hasattr(mob, "body"):
            return mob.body
        else:
            raise "Please add 'mobject' to the space first!"

    @staticmethod
    def get_shapes(mob: Mobject) -> list[pymunk.Shape] | None:
        if hasattr(mob, "shapes"):
            return mob.shapes
        else:
            raise "Please add 'mobject' to the space first!"

    def draw_debug_img(self, option: int = None) -> None:
        draw_options = pymunk.matplotlib_util.DrawOptions(ax)
        draw_options.flags = (
                pymunk.SpaceDebugDrawOptions.DRAW_SHAPES
                | pymunk.SpaceDebugDrawOptions.DRAW_COLLISION_POINTS
                # | pymunk.SpaceDebugDrawOptions.DRAW_CONSTRAINTS
            )
        if option is not None:
            draw_options.flags = option

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim(-10, 10)
        ax.set_ylim(-5, 5)
        ax.set_aspect("equal")
        self.vspace.space.debug_draw(draw_options)
        fig.show()
