
from typing import Optional
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import PinJoint

from pymunk import Space

# 已测试
class VPinJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a: list = ORIGIN,  # 以a_mob为坐标的局部坐标锚点
        anchor_b: list = ORIGIN,
        distance: Optional[float] = None,  # 手动配置距离
        mob_a_appearance: Mobject = Dot(color=RED),  # 锚点样式
        mob_b_appearance: Mobject = Dot(color=RED),  # 锚点样式
        connect_line_class: Optional[Line] = None,  # 锚点样式
        connect_line_style: dict = {
            "color": YELLOW,
            "stroke_width": 2,
        },
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        self.anchor_a_local = tuple(anchor_a[:2])
        self.anchor_b_local = tuple(anchor_b[:2])

        self.appearance_a = mob_a_appearance
        self.appearance_b = mob_b_appearance
        self.connect_line_class = connect_line_class
        self.connect_line_style = connect_line_style
        self.line = None
        self.constraint: Optional[PinJoint] = None
        self.init_distance = distance
        # 检查
        self.__check_data()

    def __check_data(self):
        # 1. 首先确保两个物体都不是 None
        if self.a_mob is None or self.b_mob is None:
            raise ValueError(
                "Constraints cannot be created without both a_mob and b_mob."
            )

        # 2. 计算两个物体的中心点距离
        dist = np.linalg.norm(self.a_mob.get_center() - self.b_mob.get_center())

        # 3. 检查重合情况
        if dist < 0.000001:
            # 如果用户明确要求绘制连接线，但在同一点，则报错
            if self.connect_line_class is not None:
                raise ValueError(
                    f"Points {self.a_mob} and {self.b_mob} are at the same location ({dist:.8f}). "
                    "Connecting them with a line makes no sense."
                )

    def install(self, space: Space):
        """由 SpaceScene 驱动安装物理约束并初始化视觉"""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VPinJoint 连接的物体必须先执行 add_dynamic_body")

        # 1. 创建约束（此时 self.anchor_a_local 已经是 tuple，直接使用）
        self.constraint = PinJoint(
            a_body, b_body, self.anchor_a_local, self.anchor_b_local
        )

        if self.init_distance is not None:
            self.constraint.distance = self.init_distance

        # 2. 同步初始视觉位置
        # 利用 Pymunk 计算当前锚点的世界坐标
        pos_a = a_body.local_to_world(self.anchor_a_local)
        pos_b = b_body.local_to_world(self.anchor_b_local)
        p1 = [pos_a.x, pos_a.y, 0]
        p2 = [pos_b.x, pos_b.y, 0]

        # 初始化直线
        if self.connect_line_class:
            self.line = self.connect_line_class(p1, p2, **self.connect_line_style)
            self.add(self.line)

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        # 统一添加子物件
        self.add(self.appearance_a, self.appearance_b)

        # 3. 注入物理世界
        space.add(self.constraint)

        # 4. 绑定实时更新
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """同步 updater：物理驱动视觉"""
        if not self.constraint:
            return

        # 此时 constraint.anchor_a 已经是底层 tuple，无需转换直接取世界坐标
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        wb = self.constraint.b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        if isinstance(self.line, Line):
            self.line.put_start_and_end_on(p1, p2)
