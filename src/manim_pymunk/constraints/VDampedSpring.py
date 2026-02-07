"""阻尼弹簧约束模块。

该模块实现VDampedSpring类，用于在两个刚体之间创建带阻尼的弹簧连接，
结合弹性和阻尼效应模拟现实的弹簧行为。
"""

from typing import Optional
from manim_pymunk.custom_mobjects import VSpring
from pymunk import Space
from pymunk.constraints import DampedSpring
from manim import *
from manim_pymunk.constraints import VConstraint


class VDampedSpring(VConstraint):
    """两个刚体之间的阻尼弹簧约束。
    
    VDampedSpring在两个刚体之间创建一个弹簧连接。当两个锚点之间的
    距离偏离静息长度时，弹簧力将其拉回；阻尼力则衰减振荡。
    
    Attributes:
        a_mob (Mobject): 第一个连接的Mobject对象。
        b_mob (Mobject): 第二个连接的Mobject对象。
        anchor_a_local (tuple): a_mob身体坐标系中的锚点。
        anchor_b_local (tuple): b_mob身体坐标系中的锚点。
        rest_length (float): 弹簧的静息长度。
        stiffness (float): 弹簧的刚度系数。
        damping (float): 阻尼系数。
        constraint (pymunk.DampedSpring): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a: np.ndarray = ORIGIN,
        anchor_b: np.ndarray = ORIGIN,
        rest_length: float = 1.0,
        stiffness: float = 100.0,
        damping: float = 10.0,
        mob_a_appearance: Mobject = Dot(color=BLUE),
        mob_b_appearance: Mobject = Dot(color=BLUE),
        connect_line_class: Optional[Line] = VSpring,
        connect_line_style: dict = {"color": YELLOW, "stroke_width": 2},
        **kwargs,
    ):
        """初始化阻尼弹簧约束。
        
        Args:
            a_mob (Mobject): 第一个连接的Mobject对象。
            b_mob (Mobject): 第二个连接的Mobject对象。
            anchor_a (np.ndarray, optional): a_mob上的锚点，默认为原点。
            anchor_b (np.ndarray, optional): b_mob上的锚点，默认为原点。
            rest_length (float, optional): 静息长度，默认为1.0。
            stiffness (float, optional): 弹簧刚度，默认为100.0。
            damping (float, optional): 阻尼系数，默认为10.0。
            mob_a_appearance (Mobject, optional): a_mob锚点的视觉表现，默认为蓝色点。
            mob_b_appearance (Mobject, optional): b_mob锚点的视觉表现，默认为蓝色点。
            connect_line_class (Optional[Line], optional): 连接线的类型，默认为VSpring。
            connect_line_style (dict, optional): 连接线的样式配置。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Pymunk compatibility: store as (x, y) tuples
        self.anchor_a_local = tuple(anchor_a[:2])
        self.anchor_b_local = tuple(anchor_b[:2])

        # Spring physics properties
        self.rest_length = rest_length
        self.stiffness = stiffness
        self.damping = damping

        self.appearance_a = mob_a_appearance
        self.appearance_b = mob_b_appearance
        self.connect_line_class = connect_line_class
        self.connect_line_style = connect_line_style
        self.conn_line: Optional[VMobject] = None
        self.constraint: Optional[DampedSpring] = None

    def install(self, space: Space):
        """安装弹簧约束并初始化视觉组件。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VDampedSpring connected objects must have a Pymunk body.")

        # 1. Create Pymunk DampedSpring
        self.constraint = DampedSpring(
            a_body,
            b_body,
            self.anchor_a_local,
            self.anchor_b_local,
            self.rest_length,
            self.stiffness,
            self.damping,
        )

        # 2. Sync initial visual position
        pos_a = a_body.local_to_world(self.anchor_a_local)
        pos_b = b_body.local_to_world(self.anchor_b_local)
        p1 = [pos_a.x, pos_a.y, 0]
        p2 = [pos_b.x, pos_b.y, 0]

        # Initialize visual representation (Simple line or custom Spring)
        if self.connect_line_class:
            self.conn_line = self.connect_line_class(p1, p2, **self.connect_line_style)

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        self.add(self.conn_line, self.appearance_a, self.appearance_b)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """实时同步弹簧的视觉表现与物理状态。
        
        根据物理引擎的计算结果，更新锚点位置和弹簧连接线。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
        if not self.constraint:
            return

        # Get world coordinates from Pymunk
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        wb = self.constraint.b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        if self.conn_line:
            self.conn_line.put_start_and_end_on(p1, p2)
