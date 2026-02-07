"""简单电动机约束模块。

该模块实现VSimpleMotor类，用于在两个刚体之间创建转矩驱动约束，
使一个刚体以指定的相对角速度旋转另一个刚体。
"""

from math import inf
from manim import *
from manim_pymunk.constraints import VConstraint
from pymunk.constraints import SimpleMotor
from pymunk import Space
from typing import Optional


class VSimpleMotor(VConstraint):
    """两个刚体之间的简单电动机约束。
    
    VSimpleMotor通过施加转矩驱动两个刚体之间的相对旋转。
    它强制刚体B相对于刚体A以指定的角速率旋转。
    
    Attributes:
        a_mob (Mobject): 基准刚体所对应的Mobject对象。
        b_mob (Mobject): 被驱动刚体所对应的Mobject对象。
        rate (float): 目标相对角速度（弧度/秒）。
        max_torque (float): 电动机能施加的最大转矩。
        constraint (pymunk.SimpleMotor): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        rate: float = 1.0,
        max_torque: float = inf,
        indicator_line_class: Optional[Line] = Arrow,
        indicator_line_style: dict = {
            "color": YELLOW,
            "stroke_width": 2,
        },
        **kwargs,
    ):
        """初始化简单电动机约束。
        
        Args:
            a_mob (Mobject): 基准刚体的Mobject对象。
            b_mob (Mobject): 被驱动刚体的Mobject对象。
            rate (float, optional): 目标相对角速度，默认为1.0弧度/秒。
            max_torque (float, optional): 最大转矩，默认为无限大。
            indicator_line_class (Optional[Line], optional): 方向指示器的类型，默认为Arrow。
            indicator_line_style (dict, optional): 方向指示器的样式配置。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Motor properties
        self.rate = rate  # Desired relative angular velocity
        self.max_torque = max_torque

        self.indicator_line_class = indicator_line_class
        self.indicator_line_style = indicator_line_style
        self.indicator_line = None
        self.constraint: Optional[SimpleMotor] = None

    def install(self, space: Space):
        """安装电动机约束并初始化旋转方向指示器。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VSimpleMotor connected objects must have Pymunk bodies.")

        # 1. Create Pymunk SimpleMotor
        self.constraint = SimpleMotor(a_body, b_body, self.rate)

        # Highly recommended for motors: limit the torque
        self.constraint.max_force = self.max_torque

        # 2. Initialize Visuals
        # A curved arrow to indicate the direction of the motor's drive
        if self.indicator_line_class is not None:
            self.indicator_line = Line(
                start=self.b_mob.get_center(),
                end=self.b_mob.get_start(),
                **self.indicator_line_style,
            )
            self.add(self.indicator_line)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """保持方向指示器与被驱动刚体同步。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
        if not self.constraint:
            return
        
        self.indicator_line.put_start_and_end_on(
            start=self.b_mob.get_center(),
            end=self.b_mob.get_start(),
        )
