from typing import Optional
import pymunk
import numpy as np
from pymunk.constraints import PinJoint
from manim import *

from pymunk.constraints import DampedRotarySpring
from pymunk.constraints import DampedSpring
from pymunk.constraints import GearJoint
from pymunk.constraints import GrooveJoint
from pymunk.constraints import PivotJoint
from pymunk.constraints import RatchetJoint
from pymunk.constraints import RotaryLimitJoint
from pymunk.constraints import SimpleMotor
from pymunk.constraints import SlideJoint


class VConstraint(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __check_data(self):
        pass
    def install(self, space: pymunk.Space):
        "安装更新器"
        pass

    def mob_updater(self, mob, dt):
        "更新器"
        pass

# 已检查
class VPinJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a: np.ndarray = ORIGIN,  # 以a_mob为坐标的局部坐标锚点
        anchor_b: np.ndarray = ORIGIN,
        distance: Optional[float] = None,  # 手动配置距离
        mob_a_appearance: Mobject = Dot(color=RED),  # 锚点样式
        mob_b_appearance: Mobject = Dot(color=RED),  # 锚点样式
        connect_line_class: Optional[Line] = None,  # 锚点样式
        connect_line_style: dict = {"color":YELLOW, "stroke_width":2,},
          ** kwargs,
    ):
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
        # 检查
        self.__check_data()

    def __check_data(self):
        # 1. 首先确保两个物体都不是 None
        if self.a_mob is None or self.b_mob is None:
            raise ValueError("Constraints cannot be created without both a_mob and b_mob.")

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
    def install(self, space: pymunk.Space):
        """由 SpaceScene 驱动安装物理约束并初始化视觉"""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VPinJoint 连接的物体必须先执行 add_dynamic_body")

        # 1. 创建约束（此时 self.anchor_a_local 已经是 tuple，直接使用）
        self.constraint = PinJoint(
            a_body, b_body, self.anchor_a_local, self.anchor_b_local
        )

        if self.init_distance is not None:
            self.constraint.distance = self.init_distance

        # 2. 同步初始视觉位置
        # 利用 Pymunk 计算当前锚点的世界坐标
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

        # 统一添加子物件
        self.add(self.appearance_a, self.appearance_b)

        # 3. 注入物理世界
        space.add(self.constraint)

        # 4. 绑定实时更新
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """同步 updater：物理驱动视觉"""
        if not self.constraint:
            return

        # 此时 constraint.anchor_a 已经是底层 tuple，无需转换直接取世界坐标
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        wb = self.constraint.b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        if isinstance(self.line, Line):
            self.line.put_start_and_end_on(p1, p2)


class VDampedRotarySpring(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        rest_angle: float = 0.0,   # 目标相对角度
        stiffness: float = 10.0,  # 刚度
        damping: float = 1.0,    # 阻尼
        arc_indicator_class: Optional[type] = Arc, 
        arc_indicator_style: dict = {"radius":0.1, "color": RED, "stroke_width": 4},
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
            raise ValueError("Constraints cannot be created without both a_mob and b_mob.")

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
            
    def install(self, space: pymunk.Space):
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
                **self.connect_line_style
            )
            self.add(self.conn_line)
        
        # 初始化两个弧形指示器
        if self.arc_indicator_class:
            # 初始状态设为极小角度，避免渲染错误
            self.arc_a = self.arc_indicator_class(angle=self.rest_angle, **self.arc_indicator_style)
            self.arc_b = self.arc_indicator_class(angle=self.rest_angle, **self.arc_indicator_style)
            self.add(self.arc_a, self.arc_b)

        # 3. 注入物理世界
        space.add(self.constraint)

        # 4. 绑定更新器
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """同步旋转状态与视觉表现"""
        if not self.constraint:
            return

        # 获取当前物理状态
        body_a = self.constraint.a
        body_b = self.constraint.b
        
        # Manim 坐标转换
        pos_a = np.array([body_a.position.x, body_a.position.y, 0])
        pos_b = np.array([body_b.position.x, body_b.position.y, 0])

        # 获取角度差 (b_mob.angle - a_mob.angle)
        # 注意：Pymunk 使用弧度，Manim 的角度属性通常也是弧度同步的
        rel_angle = body_a.angle - body_b.angle
        
        # 确保 Arc 角度不为 0 以防报错
        display_angle = rel_angle if abs(rel_angle) > 0.005 else 0.005

        # 1. 更新弧形指示器
        if self.arc_indicator_class:
            if self.arc_a:
                new_arc_a = self.arc_indicator_class(
          
                    angle=display_angle, 
                    **self.arc_indicator_style
                ).next_to(self.a_mob, UP, buff=0.1)
                self.arc_a.become(new_arc_a)
            
            if self.arc_b:
                new_arc_b = self.arc_indicator_class(
          
                    angle=-display_angle, 
                    **self.arc_indicator_style
                ).next_to(self.b_mob, DOWN, buff=0.1)
                self.arc_b.become(new_arc_b)

        # 2. 更新连接线
        if self.conn_line:
            self.conn_line.put_start_and_end_on(pos_a, pos_b)


class VDampedSpring(VConstraint):
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
        show_spring: bool = True,
        **kwargs,
    ):
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
        self.show_spring = show_spring
        self.spring_line = None
        self.constraint: Optional[DampedSpring] = None

    def install(self, space: pymunk.Space):
        """Install physics constraint and initialize visual mobjects."""
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
        if self.show_spring:
            # You can replace Line with a custom zig-zag VMobject for a "spring" look
            self.spring_line = Line(p1, p2, color=GREY_B, stroke_width=2)
        else:
            self.spring_line = VMobject()

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        self.add(self.spring_line, self.appearance_a, self.appearance_b)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Sync visual state with physics engine every frame."""
        if not self.constraint:
            return

        # Get world coordinates from Pymunk
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        wb = self.constraint.b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        if self.show_spring and isinstance(self.spring_line, Line):
            self.spring_line.put_start_and_end_on(p1, p2)

            # Optional: Dynamic coloring based on stretch
            # dist = np.linalg.norm(np.array(p1) - np.array(p2))
            # if dist > self.rest_length: self.spring_line.set_color(RED)
            # else: self.spring_line.set_color(BLUE)


class VGearJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        phase: float = 0.0,
        ratio: float = 1.0,
        show_indicator: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Gear specific properties
        self.phase = phase
        self.ratio = ratio

        self.show_indicator = show_indicator
        self.constraint: Optional[GearJoint] = None
        self.indicator = None

    def install(self, space: pymunk.Space):
        """Install the angular gear constraint into the physics space."""
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
        if self.show_indicator:
            self.indicator = DashedLine(
                self.a_mob.get_center(), self.b_mob.get_center(), color=GRAY_A
            ).set_opacity(0.5)
            self.add(self.indicator)
        else:
            self.indicator = VMobject()

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Update visual indicators to follow the bodies."""
        if not self.constraint:
            return

        # Update indicator position if it exists
        if self.show_indicator and isinstance(self.indicator, DashedLine):
            self.indicator.put_start_and_end_on(
                self.a_mob.get_center(), self.b_mob.get_center()
            )

    def set_ratio(self, new_ratio: float):
        """Helper to update gear ratio dynamically."""
        if self.constraint:
            self.constraint.ratio = new_ratio
            self.ratio = new_ratio


class VGrooveJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        groove_a: np.ndarray = LEFT,
        groove_b: np.ndarray = RIGHT,
        anchor_b: np.ndarray = ORIGIN,
        groove_color: ManimColor = WHITE,
        pivot_appearance: Mobject = Dot(color=YELLOW),
        show_groove: bool = True,
        **kwargs,
    ):
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

    def install(self, space: pymunk.Space):
        """Install physics constraint and initialize track/pivot visuals."""
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
        # Calculate world coordinates for the groove start, end, and the pivot
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
        """Sync the visual track and pivot with the physics bodies."""
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


class VPivotJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        anchor_a: Optional[np.ndarray] = None,
        anchor_b: Optional[np.ndarray] = None,
        pivot: Optional[np.ndarray] = None,
        pivot_appearance: Mobject = Dot(color=WHITE, radius=0.05),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Pymunk supports two ways to init PivotJoint:
        # 1. Provide a single world-space pivot point.
        # 2. Provide two local-space anchor points.
        self.pivot_world = tuple(pivot[:2]) if pivot is not None else None
        self.anchor_a_local = tuple(anchor_a[:2]) if anchor_a is not None else None
        self.anchor_b_local = tuple(anchor_b[:2]) if anchor_b is not None else None

        self.pivot_appearance = pivot_appearance
        self.constraint: Optional[PivotJoint] = None

    def install(self, space: pymunk.Space):
        """Install the pivot constraint and set up the visual tracker."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VPivotJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk PivotJoint based on provided arguments
        if self.pivot_world is not None:
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
        """Keep the visual dot at the physical pivot location."""
        if not self.constraint:
            return

        # Body A and Body B's anchors should overlap in world space,
        # so tracking either is fine.
        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        self.pivot_appearance.move_to([wa.x, wa.y, 0])


class VRatchetJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        phase: float = 0.0,
        ratchet: float = PI / 4,
        show_connection: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Ratchet specific properties
        # ratchet: the angle distance between "clicks"
        # phase: the initial angular offset
        self.phase = phase
        self.ratchet = ratchet

        self.show_connection = show_connection
        self.connection_line = None
        self.constraint: Optional[RatchetJoint] = None

    def install(self, space: pymunk.Space):
        """Install the rotary ratchet constraint into the physics space."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError("VRatchetJoint connected objects must have Pymunk bodies.")

        # 1. Create Pymunk RatchetJoint
        self.constraint = RatchetJoint(a_body, b_body, self.phase, self.ratchet)

        # 2. Initialize Visuals
        # Like GearJoint, this is an abstract angular constraint.
        # We can draw a dashed line between centers to indicate they are linked.
        if self.show_connection:
            self.connection_line = DashedLine(
                self.a_mob.get_center(),
                self.b_mob.get_center(),
                color=GRAY_C,
                stroke_width=1,
            )
            self.add(self.connection_line)
        else:
            self.connection_line = VMobject()

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Update visual state to track the connected bodies."""
        if not self.constraint:
            return

        if self.show_connection and isinstance(self.connection_line, DashedLine):
            self.connection_line.put_start_and_end_on(
                self.a_mob.get_center(), self.b_mob.get_center()
            )

    @property
    def current_angle(self) -> float:
        """Returns the current angle of the ratchet joint from the physics engine."""
        if self.constraint:
            return self.constraint.angle
        return 0.0


class VRotaryLimitJoint(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        min_angle: float = -PI / 4,
        max_angle: float = PI / 4,
        show_arc: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Angular limits in radians
        self.min_angle = min_angle
        self.max_angle = max_angle

        self.show_arc = show_arc
        self.arc_indicator = None
        self.constraint: Optional[RotaryLimitJoint] = None

    def install(self, space: pymunk.Space):
        """Install the rotary limit constraint and initialize visual feedback."""
        a_body = getattr(self.a_mob, "body", None)
        b_body = getattr(self.b_mob, "body", None)

        if not a_body or not b_body:
            raise ValueError(
                "VRotaryLimitJoint connected objects must have Pymunk bodies."
            )

        # 1. Create Pymunk RotaryLimitJoint
        self.constraint = RotaryLimitJoint(
            a_body, b_body, self.min_angle, self.max_angle
        )

        # 2. Initialize Visuals
        # We visualize the allowed range as an Arc centered on Body A
        if self.show_arc:
            self.arc_indicator = Arc(
                radius=0.5,
                start_angle=self.min_angle,
                angle=self.max_angle - self.min_angle,
                color=YELLOW,
                stroke_width=2,
            ).set_opacity(0.3)
            self.add(self.arc_indicator)
        else:
            self.arc_indicator = VMobject()

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Sync the visual arc with the base body's orientation."""
        if not self.constraint:
            return

        # The limit is relative to Body A's current orientation
        # We move the arc to Body A's center and rotate it to match
        base_pos = self.a_mob.get_center()
        base_angle = self.constraint.a.angle

        self.arc_indicator.move_to(base_pos)
        # Note: Manim uses absolute rotation for set_angle/rotate
        # We align the arc's 'zero' with Body A's orientation
        self.arc_indicator.set_angle(base_angle + self.min_angle)

    def set_limits(self, min_angle: float, max_angle: float):
        """Dynamically update the angular limits."""
        if self.constraint:
            self.constraint.min = min_angle
            self.constraint.max = max_angle
            self.min_angle = min_angle
            self.max_angle = max_angle
            # If visual arc exists, we would ideally recreate or scale it here


class VSimpleMotor(VConstraint):
    def __init__(
        self,
        a_mob: Mobject,
        b_mob: Mobject,
        rate: float = 1.0,
        max_torque: float = 1000.0,
        show_direction: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.a_mob = a_mob
        self.b_mob = b_mob

        # Motor properties
        self.rate = rate  # Desired relative angular velocity
        self.max_torque = max_torque

        self.show_direction = show_direction
        self.arrow_indicator = None
        self.constraint: Optional[SimpleMotor] = None

    def install(self, space: pymunk.Space):
        """Install the motor constraint and initialize the rotation indicator."""
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
        if self.show_direction:
            # Direction of arrow depends on sign of rate
            angle = PI if self.rate >= 0 else -PI
            self.arrow_indicator = CurvedArrow(
                start_point=RIGHT * 0.5,
                end_point=UP * 0.5,
                angle=angle,
                color=GOLD,
                stroke_width=3,
            ).set_opacity(0.6)
            self.add(self.arrow_indicator)
        else:
            self.arrow_indicator = VMobject()

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Keep the indicator centered on the second body (the driven body)."""
        if not self.constraint:
            return

        # Place the motor icon on the body being driven (Body B)
        # or at the midpoint if appropriate.
        self.arrow_indicator.move_to(self.b_mob.get_center())
        # The icon rotates with the body it represents
        self.arrow_indicator.set_angle(self.constraint.b.angle)

    def set_rate(self, new_rate: float):
        """Change the motor speed dynamically."""
        if self.constraint:
            self.constraint.rate = new_rate
            self.rate = new_rate


class VSlideJoint(VConstraint):
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
        show_line: bool = True,
        **kwargs,
    ):
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
        self.show_line = show_line
        self.line = None
        self.constraint: Optional[SlideJoint] = None

    def install(self, space: pymunk.Space):
        """Install physics constraint and initialize visuals."""
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
        if self.show_line:
            # We use a dashed line often for slide joints to distinguish from PinJoints
            self.line = DashedLine(p1, p2, color=GREEN_B, stroke_width=2)
        else:
            self.line = VMobject()

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        self.add(self.line, self.appearance_a, self.appearance_b)

        # 3. Inject into Pymunk space
        space.add(self.constraint)

        # 4. Bind real-time updater
        self.add_updater(self.mob_updater)

    def mob_updater(self, mob, dt):
        """Update the tether line and anchors based on physics bodies."""
        if not self.constraint:
            return

        wa = self.constraint.a.local_to_world(self.constraint.anchor_a)
        wb = self.constraint.b.local_to_world(self.constraint.anchor_b)
        p1 = [wa.x, wa.y, 0]
        p2 = [wb.x, wb.y, 0]

        self.appearance_a.move_to(p1)
        self.appearance_b.move_to(p2)

        if self.show_line and isinstance(self.line, (Line, DashedLine)):
            self.line.put_start_and_end_on(p1, p2)

            # Visual flair: Change line opacity or color when at the limit
            dist = np.linalg.norm(np.array(p1) - np.array(p2))
            if dist >= self.max_dist * 0.98 or dist <= self.min_dist * 1.02:
                self.line.set_stroke(opacity=1.0, width=3)
            else:
                self.line.set_stroke(opacity=0.4, width=2)
