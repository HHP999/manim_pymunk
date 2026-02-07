"""齿轮关节约束模块。

该模块实现VGearJoint类，用于在两个刚体之间创建齿轮约束，
强制两个刚体之间的相对旋转满足指定的齿轮比例关系。
"""

from typing import Optional
from pymunk import Space
from pymunk.constraints import GearJoint
from manim import *
from manim_pymunk.constraints import VConstraint


class VGearJoint(VConstraint):
    """两个刚体之间的齿轮约束。
    
    VGearJoint强制两个刚体之间的角度关系满足：
    (angle_b - phase) = ratio * angle_a
    
    这模拟了两个相互啮合的齿轮的行为。
    
    Attributes:
        a_mob (Mobject): 第一个齿轮对应的Mobject对象。
        b_mob (Mobject): 第二个齿轮对应的Mobject对象。
        phase (float): 初始角度偏移（弧度）。
        ratio (float): 齿轮比例（b的角速度/a的角速度）。
        constraint (pymunk.GearJoint): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        phase: float = 0.0,
        ratio: float = 1.0,
        indicator_line_class: Optional[Line] = Arrow,
        indicator_line_style: dict = {
            "color": BLUE,
            "stroke_width": 2,
        },
        **kwargs,
    ):
        """初始化齿轮约束。
        
        Args:
            a_mob (Mobject): 驱动齿轮的Mobject对象。
            b_mob (Mobject): 被驱动齿轮的Mobject对象。
            phase (float, optional): 初始角度偏移，默认为0.0。
            ratio (float, optional): 齿轮比例，默认为1.0。
            indicator_line_class (Optional[Line], optional): 旋转指示线的类型，默认为Arrow。
            indicator_line_style (dict, optional): 旋转指示线的样式配置。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Gear specific properties
        self.phase = phase
        self.ratio = ratio
        self.indicator_a = None
        self.indicator_b = None
        self.constraint: Optional[GearJoint] = None
        self.indicator_line_class = indicator_line_class
        self.indicator_line_style = indicator_line_style

    def install(self, space: Space):
        """安装齿轮约束并初始化旋转指示器。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VGearJoint connected objects must have a Pymunk body.")

        # 1. Create Pymunk GearJoint
        # Enforces: (angle_b - phase) = ratio * angle_a
        self.constraint = GearJoint(a_body, b_body, self.phase, self.ratio)

        # 2. Initialize Visuals
        # Since GearJoints are abstract angular links, we often don't draw a line.
        # However, we can add a visual indicator (like a dashed connection) if desired.
        if self.indicator_line_class:
            self.indicator_a = self.indicator_line_class(
                self.a_mob.get_center(),
                self.a_mob.get_center() + UP * 0.4,
                **self.indicator_line_style,
            )
            self.indicator_b = self.indicator_line_class(
                self.b_mob.get_center(),
                self.b_mob.get_center() + UP * 0.4,
                **self.indicator_line_style,
            )
            self.add(self.indicator_a, self.indicator_b)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """更新旋转指示器以跟踪刚体的旋转。
        
        根据两个刚体的实时旋转角度，更新指示线的朝向。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
        if not self.constraint:
            return

        a_body = self.constraint.a
        b_body = self.constraint.b

        # 指针的长度
        length = 0.4

        if self.indicator_a:
            # 计算 a_body 旋转后的末端坐标
            # a_body.angle 是弧度，我们需要计算其在世界空间的方向
            end_a = (
                self.a_mob.get_center()
                + np.array([np.cos(a_body.angle), np.sin(a_body.angle), 0]) * length
            )

            self.indicator_a.put_start_and_end_on(self.a_mob.get_center(), end_a)

        if self.indicator_b:
            # 同理计算 b_body 的末端坐标
            end_b = (
                self.b_mob.get_center()
                + np.array([np.cos(b_body.angle), np.sin(b_body.angle), 0]) * length
            )

            self.indicator_b.put_start_and_end_on(self.b_mob.get_center(), end_b)
