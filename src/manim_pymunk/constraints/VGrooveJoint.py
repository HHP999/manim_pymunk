"""滑槽关节约束模块。

该模块实现VGrooveJoint类，用于在两个刚体之间创建滑槽约束，
允许一个刚体沿着另一个刚体上的指定线段滑动。
"""

from typing import Optional
from pymunk.constraints import GrooveJoint

from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk import Space


class VGrooveJoint(VConstraint):
    """两个刚体之间的滑槽关节约束。
    
    VGrooveJoint在Body A上定义一条直线滑槽，Body B上的点被约束在
    这条滑槽内滑动。Body B可以沿滑槽自由移动，但不能离开滑槽。
    
    Attributes:
        a_mob (Mobject): 定义滑槽的Mobject对象。
        b_mob (Mobject): 在滑槽内运动的Mobject对象。
        groove_a_local (tuple): 滑槽起点，a_mob身体坐标系。
        groove_b_local (tuple): 滑槽终点，a_mob身体坐标系。
        anchor_b_local (tuple): b_mob身体坐标系中的枢轴点。
        constraint (pymunk.GrooveJoint): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        groove_a: np.ndarray = LEFT,
        groove_b: np.ndarray = RIGHT,
        anchor_b: np.ndarray = ORIGIN,
        groove_color: ManimColor = GREEN,
        pivot_appearance: Mobject = Dot(color=YELLOW),
        show_groove: bool = True,
        **kwargs,
    ):
        """初始化滑槽关节约束。
        
        Args:
            a_mob (Mobject): 定义滑槽的Mobject对象。
            b_mob (Mobject): 在滑槽内运动的Mobject对象。
            groove_a (np.ndarray, optional): 滑槽起点，默认为LEFT。
            groove_b (np.ndarray, optional): 滑槽终点，默认为RIGHT。
            anchor_b (np.ndarray, optional): b_mob上的枢轴点，默认为ORIGIN。
            groove_color (ManimColor, optional): 滑槽的颜色，默认为绿色。
            pivot_appearance (Mobject, optional): 枢轴点的视觉表现，默认为黄色点。
            show_groove (bool, optional): 是否显示滑槽线，默认为True。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Pymunk local coordinates (x, y)
        self.groove_a_local = tuple(groove_a[:2])
        self.groove_b_local = tuple(groove_b[:2])
        self.anchor_b_local = tuple(anchor_b[:2])

        self.pivot_appearance = pivot_appearance
        self.show_groove = show_groove
        self.groove_line = None
        self.constraint: Optional[GrooveJoint] = None
        self.groove_color = groove_color

    def install(self, space: Space):
        """安装滑槽约束并初始化滑槽和枢轴的视觉表现。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VGrooveJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk GrooveJoint
        self.constraint = GrooveJoint(
            a_body,
            b_body,
            self.groove_a_local,
            self.groove_b_local,
            self.anchor_b_local,
        )

        # 2. Sync initial visual position
        ga_world = a_body.local_to_world(self.groove_a_local)
        gb_world = a_body.local_to_world(self.groove_b_local)
        p_world = b_body.local_to_world(self.anchor_b_local)

        p1 = [ga_world.x, ga_world.y, 0]
        p2 = [gb_world.x, gb_world.y, 0]
        pp = [p_world.x, p_world.y, 0]

        # Initialize the groove line (the track)
        if self.show_groove:
            self.groove_line = Line(p1, p2, color=self.groove_color, stroke_width=2)
        else:
            self.groove_line = VMobject()

        self.pivot_appearance.move_to(pp)

        # Add to VConstraint
        self.add(self.groove_line, self.pivot_appearance)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """实时同步滑槽与枢轴的视觉表现。
        
        根据物理引擎的计算结果，更新滑槽线和枢轴点的位置。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
        if not self.constraint:
            return

        # Body A defines the groove track
        wa_start = self.constraint.a.local_to_world(self.constraint.groove_a)
        wa_end = self.constraint.a.local_to_world(self.constraint.groove_b)

        # Body B defines the pivot point
        wb_pivot = self.constraint.b.local_to_world(self.constraint.anchor_b)

        p1 = [wa_start.x, wa_start.y, 0]
        p2 = [wa_end.x, wa_end.y, 0]
        pp = [wb_pivot.x, wb_pivot.y, 0]

        # Update the pivot point position
        self.pivot_appearance.move_to(pp)

        # Update the groove line (it moves and rotates with Body A)
        if self.show_groove and isinstance(self.groove_line, Line):
            self.groove_line.put_start_and_end_on(p1, p2)
