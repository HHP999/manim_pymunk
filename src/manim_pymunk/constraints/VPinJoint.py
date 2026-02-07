"""固定关节约束模块。

该模块实现VPinJoint类，用于在两个刚体之间创建固定距离的连接，
约束两个锚点之间的距离保持在指定的常数值。
"""

from typing import Optional
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import PinJoint
from pymunk import Space


class VPinJoint(VConstraint):
    """两个刚体之间的固定距离关节约束。
    
    VPinJoint强制两个刚体上指定锚点之间的距离保持为常数。
    与SlideJoint不同，它不允许距离变化，仅允许旋转。
    
    Attributes:
        a_mob (Mobject): 第一个连接的Mobject对象。
        b_mob (Mobject): 第二个连接的Mobject对象。
        anchor_a_local (tuple): a_mob身体坐标系中的锚点。
        anchor_b_local (tuple): b_mob身体坐标系中的锚点。
        constraint (pymunk.PinJoint): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a: list = ORIGIN,
        anchor_b: list = ORIGIN,
        distance: Optional[float] = None,
        mob_a_appearance: Mobject = Dot(color=RED),
        mob_b_appearance: Mobject = Dot(color=RED),
        connect_line_class: Optional[Line] = None,
        connect_line_style: dict = {
            "color": YELLOW,
            "stroke_width": 2,
        },
        **kwargs,
    ):
        """初始化固定距离关节约束。
        
        Args:
            a_mob (Mobject): 第一个连接的Mobject对象。
            b_mob (Mobject): 第二个连接的Mobject对象。
            anchor_a (list, optional): a_mob上的锚点，局部坐标，默认为原点。
            anchor_b (list, optional): b_mob上的锚点，局部坐标，默认为原点。
            distance (Optional[float], optional): 固定距离，默认为None（自动计算）。
            mob_a_appearance (Mobject, optional): a_mob锚点的视觉表现，默认为红色点。
            mob_b_appearance (Mobject, optional): b_mob锚点的视觉表现，默认为红色点。
            connect_line_class (Optional[Line], optional): 连接线的类型，默认为None。
            connect_line_style (dict, optional): 连接线的样式配置。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
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
        """安装固定距离约束并初始化视觉组件。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VPinJoint 连接的物体必须先执行 add_dynamic_body")

        # 1. 创建约束
        self.constraint = PinJoint(
            a_body, b_body, self.anchor_a_local, self.anchor_b_local
        )

        if self.init_distance is not None:
            self.constraint.distance = self.init_distance

        # 2. 同步初始视觉位置
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

        self.add(self.appearance_a, self.appearance_b)

        # 3. 注入物理世界
        space.add(self.constraint)

        # 4. 绑定实时更新
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """实时同步约束的视觉表现。
        
        根据物理引擎的计算结果，更新锚点位置和连接线。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
        if not self.constraint:
            return

        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        wb = self.constraint.b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        if isinstance(self.line, Line):
            self.line.put_start_and_end_on(p1, p2)
