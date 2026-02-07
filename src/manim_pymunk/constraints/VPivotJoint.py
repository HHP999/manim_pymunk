"""枢轴关节约束模块。

该模块实现VPivotJoint类，用于在两个刚体之间创建固定点连接，
约束两个刚体在指定点处相对位置不变。
"""

from typing import Optional
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import PivotJoint
from pymunk import Space


class VPivotJoint(VConstraint):
    """两个刚体之间的枢轴关节约束。
    
    VPivotJoint在两个刚体之间创建一个固定点连接。可以通过世界坐标的
    单一枢轴点，或通过分别在两个刚体身体坐标系中的两个锚点来定义。
    
    Attributes:
        a_mob (Mobject): 第一个连接的Mobject对象。
        b_mob (Mobject): 第二个连接的Mobject对象。
        pivot_world (tuple): 世界坐标系中的枢轴点。
        anchor_a_local (tuple): a_mob身体坐标系中的锚点。
        anchor_b_local (tuple): b_mob身体坐标系中的锚点。
        constraint (pymunk.PivotJoint): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        pivot: list = None,
        anchor_a: list = None,
        anchor_b: list = None,
        pivot_appearance: Mobject = Dot(color=WHITE, radius=0.05),
        **kwargs,
    ):
        """初始化枢轴关节约束。
        
        支持两种初始化方式：
        1. 提供世界坐标系中的单一枢轴点(pivot)
        2. 提供两个身体坐标系中的锚点(anchor_a和anchor_b)
        
        Args:
            a_mob (Mobject): 第一个连接的Mobject对象。
            b_mob (Mobject): 第二个连接的Mobject对象。
            pivot (list, optional): 世界坐标系中的枢轴点，默认为None。
            anchor_a (list, optional): a_mob身体坐标系中的锚点，默认为None。
            anchor_b (list, optional): b_mob身体坐标系中的锚点，默认为None。
            pivot_appearance (Mobject, optional): 枢轴点的视觉表现，默认为白色点。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        self.pivot_world = tuple(pivot[:2]) if pivot is not None else None
        self.anchor_a_local = tuple(anchor_a[:2]) if anchor_a is not None else None
        self.anchor_b_local = tuple(anchor_b[:2]) if anchor_b is not None else None

        self.pivot_appearance = pivot_appearance
        self.constraint: Optional[PivotJoint] = None

    def install(self, space: Space):
        """安装枢轴约束并初始化枢轴位置跟踪器。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VPivotJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk PivotJoint based on provided arguments
        if self.pivot_world:
            # Init via world coordinates
            self.constraint = PivotJoint(a_body, b_body, self.pivot_world)
        elif self.anchor_a_local is not None and self.anchor_b_local is not None:
            # Init via two local anchor points
            self.constraint = PivotJoint(
                a_body, b_body, self.anchor_a_local, self.anchor_b_local
            )
        else:
            # Default to current center of both bodies if nothing provided
            self.constraint = PivotJoint(a_body, b_body, a_body.position)

        # 2. Initial Visual Placement
        # We use anchor_a to track the visual pivot point in the world
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        self.pivot_appearance.move_to([wa.x, wa.y, 0])
        self.add(self.pivot_appearance)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """保持视觉枢轴点与物理枢轴点同步。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
        if not self.constraint:
            return

        # Body A and Body B's anchors should overlap in world space,
        # so tracking either is fine.
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        self.pivot_appearance.move_to([wa.x, wa.y, 0])
