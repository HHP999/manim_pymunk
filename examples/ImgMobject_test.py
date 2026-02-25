from manim import *
from manim_pymunk import *
from pathlib import Path

# 获取资源目录
ASSETS_DIR = Path(__file__).parent / "assets"


class ImageMobjectTest(SpaceScene):
    def construct(self):
        # --- 1. 场景配置 ---
        self.add(self.camera.frame)
        self.camera.frame.scale(2)

        # --- 2. 批量加载图片并配置物理属性 ---
        # 统一资源列表
        img_names = [
            "ak47.png",
            "awm.png",
            "football.png",
            "github.png",
            "trislof.png",
        ] + ["bullts.png"] * 9  # 批量添加子弹

        images = Group(
            *[ImageMobject(ASSETS_DIR / name).scale(0.5) for name in img_names]
        )

        # 布局：在上方排列并给予随机偏移，增加下落的美感
        images.arrange_in_grid(rows=2, buff=1.0).shift(UP * 12)
        for img in images:
            img.shift(RIGHT * np.random.uniform(-2, 2))

        # --- 3. 环境配置 ---
        # 倾斜的地面让物体产生滚动
        ground = Line(LEFT * 20 + DOWN * 2, RIGHT * 20 + DOWN * 5, stroke_width=10)

        # --- 4. 复杂形状配置 ---
        # 创建一个空心容器（is_solid=False 允许物体掉进内部）
        hollow_box = Square(side_length=4, color=YELLOW, stroke_width=8).shift(
            LEFT * 5 + UP * 2
        )
        images[0].move_to(hollow_box)
        # 动力学物体：苹果与方块
        # 假设 Apple 是你定义的自定义类，确保它能被 Pymunk 正确识别形状
        falling_square = Square(side_length=1.5, fill_opacity=1, color=RED).shift(
            UP * 8 + LEFT * 5
        )

        # 静态锚点
        anchor_p1 = Dot(UP * 5 + RIGHT * 5, color=WHITE)
        anchor_p2 = Dot(UP * 5 + RIGHT * 8, color=WHITE)

        # 动态摆锤
        pendulum_bob = Circle(radius=0.5, fill_opacity=1, color=BLUE).move_to(
            RIGHT * 5 + UP * 2
        )
        spring_box = Square(side_length=0.8, fill_opacity=1, color=ORANGE).move_to(
            RIGHT * 8 + UP * 2
        )

        # 注册图片动力学刚体
        self.add_dynamic_body(*images, elasticity=0.6, friction=0.5)
        self.add_static_body(ground, friction=1.0, elasticity=0.5)
        self.add_dynamic_body(falling_square, density=2.0)
        self.add_dynamic_body(hollow_box, is_solid=False)
        self.add_static_body(anchor_p1, anchor_p2)
        self.add_dynamic_body(pendulum_bob, spring_box)

        # --- 5. 约束与关节 (Joints) ---

        # A. 销钉关节 (钉子连接)
        joint = VPinJoint(
            anchor_p1,
            pendulum_bob,
            connect_line_class=Line,
            connect_line_style={"stroke_width": 2, "color": RED},
        )

        # B. 阻尼弹簧 (弹性连接)
        spring = VDampedSpring(
            anchor_p2,
            spring_box,
            rest_length=2.0,
            stiffness=100,  # 刚度
            damping=5,  # 阻尼
            connect_line_class=DashedLine,
        )

        self.add_constraints(joint, spring)

        # --- 6. 运行与镜头动画 ---
        self.wait(2)

        # 镜头平滑追踪
        self.play(
            self.camera.frame.animate.shift(RIGHT * 4 + DOWN * 2),
            run_time=4,
            rate_func=linear,
        )
        # 最后的缩放观察全局
        self.play(self.camera.frame.animate.scale(1.5), run_time=2)
        self.wait(3)

        # # 调试辅助：在需要时导出当前的物理分布图
        # self.draw_debug_img(xlim=(-15, 15), ylim=(-10, 10))
