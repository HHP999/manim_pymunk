"""棘轮关节约束模块。

该模块实现VRatchetJoint类，用于在两个刚体之间创建棘轮约束，
强制两个刚体之间的相对旋转以固定的"棘齿"增量进行。
"""

from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import RatchetJoint
from pymunk import Space
from typing import Optional


class VRatchetJoint(VConstraint):
    """两个刚体之间的棘轮约束。
    
    VRatchetJoint强制body_b相对于body_a的角度以"棘齿"(ratchet)为单位增量。
    当两个刚体之间的相对角度不符合棘齿增量时，约束会施加转矩将其
    调整回最近的有效棘齿位置。
    
    Attributes:
        a_mob (Mobject): 基准刚体的Mobject对象。
        b_mob (Mobject): 被约束刚体的Mobject对象。
        phase (float): 初始角度偏移（弧度）。
        ratchet (float): 棘齿角度间隔（弧度）。
        constraint (pymunk.RatchetJoint): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        phase: float = 0.0,
        ratchet: float = PI / 2,
        indicator_line_class: Optional[Line] = Arrow,
        indicator_line_style: dict = {
            "color": BLUE,
            "stroke_width": 2,
        },
        indicator_line_length=0.4,
        connect_line_class: Optional[type] = Line,
        connect_line_style: dict = {"color": YELLOW, "stroke_width": 2},
        **kwargs,
    ):
        """初始化棘轮约束。
        
        Args:
            a_mob (Mobject): 基准刚体的Mobject对象。
            b_mob (Mobject): 被约束刚体的Mobject对象。
            phase (float, optional): 初始角度偏移，默认为0.0。
            ratchet (float, optional): 棘齿间隔，默认为π/2。
            indicator_line_class (Optional[Line], optional): 旋转指示线的类型，默认为Arrow。
            indicator_line_style (dict, optional): 旋转指示线的样式配置。
            indicator_line_length (float, optional): 指示线长度，默认为0.4。
            connect_line_class (Optional[type], optional): 连接线的类型，默认为Line。
            connect_line_style (dict, optional): 连接线的样式配置。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Ratchet specific properties
        self.phase = phase
        self.ratchet = ratchet
        # 样式配置存储
        self.indicator_line_class = indicator_line_class
        self.indicator_line_style = indicator_line_style
        self.indicator_line_length = indicator_line_length
        self.connect_line_class = connect_line_class
        self.connect_line_style = connect_line_style

        # 视觉组件占位
        self.indicator_a = None
        self.indicator_b = None
        self.conn_line: Optional[VMobject] = None
        self.constraint: Optional[RatchetJoint] = None
        self.__check_data()

    def __check_data(self):
        """验证约束参数的合法性。
        
        检查两个Mobject是否为None以及是否在同一位置。
        
        Raises:
            ValueError: 如果两个Mobject为None或位置重合且需要绘制连接线。
        """
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
        """安装棘轮约束并初始化视觉指示器。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VRatchetJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk RatchetJoint
        self.constraint = RatchetJoint(a_body, b_body, self.phase, self.ratchet)

        # 2. Initialize Visuals
        if self.connect_line_class:
            self.conn_line = self.connect_line_class(
                self.a_mob.get_center(),
                self.b_mob.get_center(),
                **self.connect_line_style,
            )
            self.add(self.conn_line)

        if self.indicator_line_class:
            self.indicator_a = self.indicator_line_class(
                self.a_mob.get_center(),
                self.a_mob.get_center() + UP * self.indicator_line_length,
                **self.indicator_line_style,
            )
            self.indicator_b = self.indicator_line_class(
                self.b_mob.get_center(),
                self.b_mob.get_center() + UP * self.indicator_line_length,
                **self.indicator_line_style,
            )
            self.add(self.indicator_a, self.indicator_b)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """实时更新连接线和旋转指示器。
        
        根据刚体的实时位置和旋转角度，更新所有视觉组件。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
        if not self.constraint:
            return
        a_body = self.constraint.a
        b_body = self.constraint.b
        
        # 直线更新
        if self.conn_line:
            self.conn_line.put_start_and_end_on(
                self.a_mob.get_center(), self.b_mob.get_center()
            )

        if self.indicator_a:
            end_a = (
                self.a_mob.get_center()
                + np.array([np.cos(a_body.angle), np.sin(a_body.angle), 0])
                * self.indicator_line_length
            )
            self.indicator_a.put_start_and_end_on(self.a_mob.get_center(), end_a)

        if self.indicator_b:
            end_b = (
                self.b_mob.get_center()
                + np.array([np.cos(b_body.angle), np.sin(b_body.angle), 0])
                * self.indicator_line_length
            )
            self.indicator_b.put_start_and_end_on(self.b_mob.get_center(), end_b)
