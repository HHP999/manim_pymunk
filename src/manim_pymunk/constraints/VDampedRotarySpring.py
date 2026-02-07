"""阻尼旋转弹簧约束模块。

该模块实现VDampedRotarySpring类，用于在两个刚体之间创建旋转弹簧约束，
提供一个目标相对角度，通过弹簧力和阻尼力维持该角度。
"""

from manim import *
from typing import Optional
from manim_pymunk.constraints import VConstraint
from pymunk import Space
from pymunk.constraints import DampedRotarySpring


class VDampedRotarySpring(VConstraint):
    """两个刚体之间的阻尼旋转弹簧约束。
    
    VDampedRotarySpring在两个刚体之间创建一个旋转弹簧连接。当实际相对角度
    偏离目标角度时，弹簧转矩将其拉回；阻尼转矩则衰减振荡。
    
    Attributes:
        a_mob (Mobject): 第一个连接的Mobject对象。
        b_mob (Mobject): 第二个连接的Mobject对象。
        rest_angle (float): 目标相对旋转角（弧度）。
        stiffness (float): 旋转弹簧的刚度系数。
        damping (float): 旋转阻尼系数。
        constraint (pymunk.DampedRotarySpring): 底层Pymunk约束对象。
    """

    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        rest_angle: float = 0.0,
        stiffness: float = 10.0,
        damping: float = 1.0,
        arc_indicator_class: Optional[type] = Arc,
        arc_indicator_style: dict = {"radius": 0.1, "color": RED, "stroke_width": 4},
        connect_line_class: Optional[type] = None,
        connect_line_style: dict = {"color": YELLOW, "stroke_width": 2},
        **kwargs,
    ):
        """初始化阻尼旋转弹簧约束。
        
        Args:
            a_mob (Mobject): 第一个连接的Mobject对象。
            b_mob (Mobject): 第二个连接的Mobject对象。
            rest_angle (float, optional): 目标相对角度，默认为0.0。
            stiffness (float, optional): 旋转弹簧刚度，默认为10.0。
            damping (float, optional): 旋转阻尼系数，默认为1.0。
            arc_indicator_class (Optional[type], optional): 弧形指示器的类型，默认为Arc。
            arc_indicator_style (dict, optional): 弧形指示器的样式配置。
            connect_line_class (Optional[type], optional): 连接线的类型，默认为None。
            connect_line_style (dict, optional): 连接线的样式配置。
            **kwargs: 传递给父类VConstraint的其他参数。
        """
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
        self.constraint: Optional[DampedRotarySpring] = None
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
        """安装旋转弹簧约束并初始化视觉组件。
        
        Args:
            space (pymunk.Space): 目标物理空间对象。
        
        Raises:
            ValueError: 如果连接的Mobject没有body属性。
        """
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
        """实时同步旋转状态与视觉表现。
        
        根据两个刚体的实时位置和旋转角度，更新弧形指示器和连接线。
        
        Args:
            mob (Mobject): 约束对象本身。
            dt (float): 帧时间增量（秒）。
        """
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
            new_arc_a.rotate(
                line_angle - display_angle / 2 + PI, about_point=target_pos_a
            )
            self.arc_a.become(new_arc_a)

        if self.arc_b:
            new_arc_b = self.arc_indicator_class(
                angle=-display_angle, **self.arc_indicator_style
            )
            target_pos_b = pos_b + unit_vec * (self.b_mob.get_width() / 2 + buff)
            new_arc_b.move_to(target_pos_b)
            new_arc_b.rotate(
                line_angle - (-display_angle) / 2, about_point=target_pos_b
            )
            self.arc_b.become(new_arc_b)
