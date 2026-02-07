"""滑动关节约束模块。

该模块实现VSlideJoint类，用于在两个刚体之间创建距离受限的滑动约束。
允许两个锚点之间的距离在最小值和最大值之间变化。
"""

from tracemalloc import start
from typing import Optional
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import SlideJoint
from pymunk import Space


class VSlideJoint(VConstraint):
    """两个刚体之间的滑动关节约束。
    
    VSlideJoint限制两个刚体上指定锚点之间的距离在[min_dist, max_dist]范围内。
    与PinJoint不同，它允许锚点间的距离在指定范围内自由变化。
    
    Attributes:
        a_mob (Mobject): 第一个连接的Mobject对象。
        b_mob (Mobject): 第二个连接的Mobject对象。
        anchor_a_local (tuple): 以a_mob身体坐标系计算的锚点。
        anchor_b_local (tuple): 以b_mob身体坐标系计算的锚点。
        min_dist (float): 两锚点间的最小距离。
        max_dist (float): 两锚点间的最大距离。
        constraint (pymunk.SlideJoint): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a: np.ndarray = ORIGIN,
        anchor_b: np.ndarray = ORIGIN,
        min_dist: float = 0.0,
        max_dist: float = 1.0,
        mob_a_appearance: Mobject = Dot(color=GREEN_A, radius=0.08),
        mob_b_appearance: Mobject = Dot(color=GREEN_A, radius=0.08),
        indicator_line_class: Optional[Line] = Line,
        indicator_line_style: dict = {
            "color": RED,
            "stroke_width": 2,
        },
        **kwargs,
    ):
        """初始化滑动关节约束。
        
        Args:
            a_mob (Mobject): 第一个连接的Mobject对象。
            b_mob (Mobject): 第二个连接的Mobject对象。
            anchor_a (np.ndarray, optional): a_mob上的锚点，局部坐标，默认为原点。
            anchor_b (np.ndarray, optional): b_mob上的锚点，局部坐标，默认为原点。
            min_dist (float, optional): 最小距离，默认为0.0。
            max_dist (float, optional): 最大距离，默认为1.0。
            mob_a_appearance (Mobject, optional): a_mob锚点的视觉表现，默认为绿色点。
            mob_b_appearance (Mobject, optional): b_mob锚点的视觉表现，默认为绿色点。
            indicator_line_class (Optional[Line], optional): 连接线的类型，默认为Line。
            indicator_line_style (dict, optional): 连接线的样式配置。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Pymunk local coordinates
        self.anchor_a_local = tuple(anchor_a[:2])
        self.anchor_b_local = tuple(anchor_b[:2])

        # Slide limits
        self.min_dist = min_dist
        self.max_dist = max_dist

        self.appearance_a = mob_a_appearance
        self.appearance_b = mob_b_appearance
        self.indicator_line_class = indicator_line_class
        self.indicator_line_style = indicator_line_style
        self.indicator_line = None
        self.constraint: Optional[SlideJoint] = None

    def install(self, space: Space):
        """安装滑动关节约束并初始化视觉组件。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VSlideJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk SlideJoint
        self.constraint = SlideJoint(
            a_body,
            b_body,
            self.anchor_a_local,
            self.anchor_b_local,
            self.min_dist,
            self.max_dist,
        )

        # 2. Sync initial visual position
        pos_a = a_body.local_to_world(self.anchor_a_local)
        pos_b = b_body.local_to_world(self.anchor_b_local)
        p1 = [pos_a.x, pos_a.y, 0]
        p2 = [pos_b.x, pos_b.y, 0]

        # Initialize the connection line
        if self.indicator_line_class:
            self.indicator_line = self.indicator_line_class(
                start=p1, end=p2, **self.indicator_line_style
            )
            self.add(self.indicator_line)

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        self.add(self.appearance_a, self.appearance_b)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """实时同步约束的视觉表现。
        
        根据物理引擎计算的刚体位置和角度，更新锚点位置和连接线。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
        if not self.constraint:
            return

        # 获取两个锚点的世界坐标
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        wb = self.constraint.b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        # 更新锚点视觉位置
        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        # 更新连接线
        if self.indicator_line:
            self.indicator_line.put_start_and_end_on(p1, p2)
