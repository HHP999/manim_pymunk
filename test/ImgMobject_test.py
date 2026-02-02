from manim import *
from manim_pymunk import *


class ConstraintsTest(SpaceScene):
    def construct(self):
        self.add(self.camera.frame)
        self.camera.frame.scale(2)

        imgs_filenames = [
            "ak47.png",
            "awm.png",
            "bullts.png",
            "bullts.png",
            "bullts.png",
            "bullts.png",
            "bullts.png",
            "bullts.png",
            "bullts.png",
            "bullts.png",
            "bullts.png",
            "football.png",
            "github.png",
            "trislof.png",
        ]

        img_group = Group()
        for img in imgs_filenames:
            img_group.add(ImageMobject(filename_or_array=fr"./assets/{img}"))
        img_group.arrange(UP).shift(UP*10)
        self.add_dynamic_body(*img_group)
        # 1. 配置静态地面
        ground = Line(LEFT * 30 + DOWN * 2, RIGHT * 30 + DOWN * 6, stroke_width=20)
        self.add_static_body(ground)

        # 2. 创建并配置动态物体 (小球组)
        pendulums = VGroup(*[Dot(radius=0.2) for _ in range(10)])

        apple = Apple(
            stroke_width=10,
            stroke_color=RED,
            fill_color=YELLOW,
            fill_opacity=1,
        )
        # 给小球添加内部细节（如指针），方便观察旋转
        for dot in pendulums:
            indicator = Line(
                dot.get_center(), dot.get_center() + RIGHT * 0.2, color=BLUE
            )
            dot.add(indicator)

        pendulums.arrange_in_grid(rows=1, buff=1.0)
        square_hollow = Square(color=YELLOW, stroke_width=10).move_to(pendulums[-1])
        # 创建一个跟随的小方块
        falling_square = Square(
            side_length=1,
            stroke_width=10,
            stroke_color=RED,
            fill_color=YELLOW,
            fill_opacity=1,
        )

        # 注册动态物体
        self.add_dynamic_body(*pendulums, falling_square, apple)
        self.add_dynamic_body(square_hollow, is_solid=False)

        # 3. 配置静态锚点与约束
        # 锚点 1：固定在左上方
        anchor_top = Dot(UP * 3 + LEFT * 3, color=YELLOW)

        # 锚点 2：位于第一个小球下方
        anchor_mid = Dot(color=YELLOW).next_to(anchor_top, DOWN, buff=0.6)

        # 连接到锚点 2 的方块
        box_at_anchor = (
            Circle(radius=0.5, stroke_width=10).move_to(anchor_mid).shift(RIGHT * 0.5)
        )

        self.add_static_body(anchor_top, anchor_mid)
        self.add_dynamic_body(box_at_anchor)

        # 4. 创建物理约束 (Joints)
        # 约束 A：将顶部锚点与第一个小球连接
        joint_top = VPinJoint(
            anchor_top,
            pendulums[0],
            connect_line_class=Line,
            connect_line_style={"stroke_width": 2, "color": WHITE},
        )

        vDampedSpring = VDampedSpring(
            anchor_mid,
            box_at_anchor,
            rest_length=0.5,
            stiffness=1,
            damping=1,
        )
        self.add_constraints_body(joint_top, vDampedSpring)
        # self.wait(3)
        # self.play(self.camera.frame.animate.shift(RIGHT * 3), run_time=3)
        # self.wait(3)
        # self.play(self.camera.frame.animate.scale(2), run_time=3)
        self.draw_debug_img(xlim=(-12,12), ylim=(-6,6))