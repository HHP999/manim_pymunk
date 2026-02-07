from manim import *
from manim_pymunk import *

class ConstraintsTest(SpaceScene):
    def construct(self):
        # 1. 创建组件
        # 固定锚点 A
        anchor = Dot(UP * 2, color=BLUE)
        # 悬挂点 B (初始位置设为最小距离附近，这样可以看到明显的拉伸过程)
        bob = Dot(UP * 1.5, color=WHITE) 
        # 配重 C (连接在 B 下方，增加惯性)
        weight = Square(side_length=0.5, color=ORANGE).next_to(anchor, UP, buff=2)

        # 2. 物理初始化
        self.add_static_body(anchor)
        self.add_dynamic_body(bob, weight)
        self.add_shape_filter(anchor, bob, weight, group=1)

        # 3. 创建 VSlideJoint (核心演示)
        # 允许距离在 0.5 到 3.0 之间自由滑动
        slide = VSlideJoint(
            anchor, bob,
            min_dist=0.5,
            max_dist=2.0,
            indicator_line_style={"color": RED, "stroke_width": 4}
        )

        # 4. 创建 VPinJoint (连接 B 和 C 形成双节摆)
        pin = VPinJoint(bob, weight, color=YELLOW, connect_line_class=Line)

        # 5. 添加约束
        self.add_constraints_body(slide, pin)

        # 6. 【关键】给一个水平冲量，让它摆动起来
        # 如果只是垂直掉落，视觉效果很死板
        bob.body.apply_impulse_at_local_point((15, 0)) 

        self.wait(6)