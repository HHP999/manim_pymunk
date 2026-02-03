
from manim import *
from typing import Optional
from manim_pymunk.constraints import VConstraint
from pymunk import Space
from pymunk.constraints import DampedRotarySpring

# 已测试
class VDampedRotarySpring(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        rest_angle: float = 0.0,  # 目标相对角度
        stiffness: float = 10.0,  # 刚度
        damping: float = 1.0,  # 阻尼
        arc_indicator_class: Optional[type] = Arc,
        arc_indicator_style: dict = {"radius": 0.1, "color": RED, "stroke_width": 4},
        connect_line_class: Optional[type] = None,
        connect_line_style: dict = {"color": YELLOW, "stroke_width": 2},
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
        self.arc_indicator_style = arc_indicator_style
        self.connect_line_class = connect_line_class
        self.connect_line_style = connect_line_style

        # 视觉组件占位
        self.arc_a: Optional[VMobject] = None
        self.arc_b: Optional[VMobject] = None
        self.conn_line: Optional[VMobject] = None
        self.constraint: Optional[pymunk.DampedRotarySpring] = None
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
        """由 SpaceScene 驱动安装"""
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
                **self.connect_line_style,
            )
            self.add(self.conn_line)

        # 初始化两个弧形指示器
        if self.arc_indicator_class:
            # 初始状态设为极小角度，避免渲染错误
            self.arc_a = self.arc_indicator_class(
                angle=self.rest_angle, **self.arc_indicator_style
            )
            self.arc_b = self.arc_indicator_class(
                angle=self.rest_angle, **self.arc_indicator_style
            )
            self.add(self.arc_a, self.arc_b)

        # 3. 注入物理世界
        space.add(self.constraint)

        # 4. 绑定更新器
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """同步旋转状态与视觉表现：实现对角对称"""
        if not self.constraint:
            return
        # 直线更新
        if self.conn_line:
            self.conn_line.put_start_and_end_on(
                self.a_mob.get_center(), self.b_mob.get_center()
            )
        # 1. 获取物理状态
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
                angle=display_angle, **self.arc_indicator_style
            )
            target_pos_a = pos_a - unit_vec * (self.a_mob.get_width() / 2 + buff)
            new_arc_a.move_to(target_pos_a)

            # 微调旋转：连线角度 - 弧度的一半，使弧线中点落在直线上
            new_arc_a.rotate(
                line_angle - display_angle / 2 + PI, about_point=target_pos_a
            )
            self.arc_a.become(new_arc_a)

        if self.arc_b:
            # 为了对称，b 处的弧度使用相反方向
            new_arc_b = self.arc_indicator_class(
                angle=-display_angle, **self.arc_indicator_style
            )
            target_pos_b = pos_b + unit_vec * (self.b_mob.get_width() / 2 + buff)
            new_arc_b.move_to(target_pos_b)

            # 微调旋转：连线角度 - 弧度的一半 (注意此时 display_angle 是负的，依然适用)
            new_arc_b.rotate(
                line_angle - (-display_angle) / 2, about_point=target_pos_b
            )
            self.arc_b.become(new_arc_b)
