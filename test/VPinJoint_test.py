from random import choice
from manim import *
from manim_pymunk import *

# 获取所有预定义颜色
COLORS = [getattr(AS2700, item) for item in dir(AS2700) if item.isupper()]

class ConstraintsTest(SpaceScene):
    def construct(self):
        # 1. 配置静态地面
        ground = Line(LEFT * 5 + DOWN * 2, RIGHT * 5 + DOWN * 3)
        self.add_static_body(ground)

        # 2. 创建并配置动态物体 (小球组)
        pendulums = VGroup(*[
            Dot(radius=0.2, color=choice(COLORS))
            for _ in range(3)
        ])
        
        # 给小球添加内部细节（如指针），方便观察旋转
        for dot in pendulums:
            indicator = Line(dot.get_center(), dot.get_center() + RIGHT * 0.2, color=BLUE)
            dot.add(indicator)
        
        pendulums.arrange_in_grid(rows=1, buff=1.0)
        
        # 创建一个跟随的小方块
        falling_square = Square(side_length=0.4, fill_color=YELLOW, fill_opacity=1)
        
        # 注册动态物体
        self.add_dynamic_body(*pendulums, falling_square)

        # 3. 配置静态锚点与约束
        # 锚点 1：固定在左上方
        anchor_top = Dot(UP * 3 + LEFT * 3, color=YELLOW)
        
        # 锚点 2：位于第一个小球下方
        anchor_mid = Dot(color=YELLOW).next_to(pendulums[0], DOWN, buff=0.7)
        
        # 连接到锚点 2 的方块
        box_at_anchor = Square(side_length=1.2).move_to(anchor_mid)
        
        self.add_static_body(anchor_top, anchor_mid)
        self.add_dynamic_body(box_at_anchor)

        # 4. 创建物理约束 (Joints)
        # 约束 A：将顶部锚点与第一个小球连接
        joint_top = VPinJoint(
            anchor_top,
            pendulums[0],
            connect_line_class=Line,
            connect_line_style={"stroke_width": 2, "color": WHITE}
        )

        # 约束 B：将中间锚点与方块连接
        joint_mid = VPinJoint(
            anchor_mid,
            box_at_anchor,
        )

        # 5. 配置碰撞过滤 (避免锚点与连接物体自撞)
        self.add_shape_filter(anchor_mid, box_at_anchor, group=2)

        # 6. 将约束添加到物理世界并开跑
        self.add_constraints_body(joint_top, joint_mid)

        self.wait(5)