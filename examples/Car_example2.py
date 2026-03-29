import random
from manim import *
from manim_pymunk import *
from pathlib import Path
import svgelements as se
from PIL import Image


class Car(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        width, height, wheel_radius = 2.5, 1.5, 1
        self.body = Rectangle(width=width, height=height, color=BLUE, fill_opacity=0.8)

        p_B_body = self.body.get_corner(DL)
        p_C_body = self.body.get_corner(DR)

        self.back_wheel = Circle(radius=wheel_radius, color=WHITE, fill_opacity=1)
        self.back_wheel.move_to(p_B_body + LEFT * 1.5 + DOWN * 0.5)

        self.front_wheel = Circle(radius=wheel_radius, color=WHITE, fill_opacity=1)
        self.front_wheel.move_to(p_C_body + RIGHT * 1.5 + DOWN * 0.5)

        pos_B = (
            self.front_wheel.get_center() + (wheel_radius + 0.3) * RIGHT + DOWN * 0.5
        )
        pos_C = pos_B + RIGHT * 1.8
        pos_A = pos_B + UP * 1

        self.shovel = Polygon(pos_A, pos_B, pos_C, color=ORANGE, fill_opacity=0.9)
        print(self.shovel.get_vertices())
        self.add(self.body, self.back_wheel, self.front_wheel, self.shovel)

    def add_constraints(self, static_body):
        # 1. 基础点位获取
        # 统一获取中心点，用于计算相对偏移
        body_center = self.body.get_center()
        # 1. 计算相对偏移（局部坐标）
        # 这样无论 move_to 到哪，结果都是固定的偏移量
        loc_A = self.body.get_corner(UL) - body_center
        loc_B = self.body.get_corner(DL) - body_center
        loc_C = self.body.get_corner(DR) - body_center
        loc_D = self.body.get_corner(UR) - body_center

        # 铲斗顶点坐标（用于物理锚点参考）
        # 注意：Manim-Pymunk 内部需要相对于各自 Mobject 中心的相对坐标
        s_A = self.shovel.get_vertices()[0]
        s_B = self.shovel.get_vertices()[1]
        print(self.shovel.get_vertices())

        # 2. 原有的车轮旋转销钉 (A-后轮, D-前轮)
        pivots = [
            VPinJoint(
                self.body,
                self.back_wheel,
                anchor_a_local=loc_A,
                anchor_b_local=ORIGIN,
                connect_line_class=Line,
                anchor_a_appearance=VMobject(),
                anchor_b_appearance=VMobject(),
            ),
            VPinJoint(
                self.body,
                self.front_wheel,
                anchor_a_local=loc_D,
                anchor_b_local=ORIGIN,
                connect_line_class=Line,
                anchor_a_appearance=VMobject(),
                anchor_b_appearance=VMobject(),
            ),
        ]

        shovel_locks = [
            VPinJoint(
                self.body,
                self.shovel,
                anchor_a_local=loc_C,
                anchor_b_local=s_A - self.shovel.get_center(),
                # connect_line_class=Line,
                anchor_a_appearance=VMobject(),
                anchor_b_appearance=VMobject(),
            ),
            VPinJoint(
                self.body,
                self.shovel,
                anchor_a_local=loc_D,
                anchor_b_local=s_A - self.shovel.get_center(),
                # connect_line_class=Line,
                anchor_a_appearance=VMobject(),
                anchor_b_appearance=VMobject(),
            ),
            VPinJoint(
                self.body,
                self.shovel,
                anchor_a_local=loc_C,
                anchor_b_local=s_B - self.shovel.get_center(),
                # connect_line_class=Line,
                anchor_a_appearance=VMobject(),
                anchor_b_appearance=VMobject(),
            ),
            VPinJoint(
                self.body,
                self.shovel,
                anchor_a_local=loc_D,
                anchor_b_local=s_B - self.shovel.get_center(),
                # connect_line_class=Line,
                anchor_a_appearance=VMobject(),
                anchor_b_appearance=VMobject(),
            ),
        ]

        rest_dist = np.linalg.norm(
            self.back_wheel.get_center() - self.front_wheel.get_center()
        )
        horizontal_spring = VDampedSpring(
            self.back_wheel,
            self.front_wheel,
            rest_length=rest_dist,
            stiffness=500,
            damping=30,
            connect_line_config={"turns": 18, "color": RED, "stroke_width": 4},
        )

        suspensions = [
            VDampedSpring(
                self.body,
                self.back_wheel,
                anchor_a_local=loc_B,
                rest_length=np.linalg.norm(
                    self.body.get_corner(DL) - self.back_wheel.get_center()
                ),
                stiffness=400,
                damping=15,
                connect_line_config={"turns": 8, "color": RED, "stroke_width": 4},
            ),
            VDampedSpring(
                self.body,
                self.front_wheel,
                anchor_a_local=loc_C,
                rest_length=np.linalg.norm(
                    self.body.get_corner(DR) - self.front_wheel.get_center()
                ),
                stiffness=400,
                damping=15,
                connect_line_config={"turns": 8, "color": RED, "stroke_width": 4},
            ),
        ]

        # 5. 马达
        motors = [
            VSimpleMotor(self.body, self.back_wheel, rate=15, max_torque=1000),
            VSimpleMotor(self.body, self.front_wheel, rate=15, max_torque=1000),
        ]

        # 6. 旋转限制 (修正版)
        # 注意：我们需要限制的是 body 相对于“世界(静态空间)”的角度
        # 而不是相对于会旋转的轮子
        rotary_limits = [
            VRotaryLimitJoint(
                self.body,
                static_body,  # 关键：连接到静态背景
                min_angle=-60 * DEGREES,
                max_angle=60 * DEGREES,
            )
        ]
        return [
            *rotary_limits,
            *suspensions,
            *pivots,
            *shovel_locks,
            horizontal_spring,
            *motors,
        ]


ASSETS_DIR = Path(__file__).parent / "assets"


class SpaceSceneExample(SpaceScene):
    def construct(self):
        self.add(self.camera.frame)
        self.camera.frame.scale(2)

        # physics
        all_items_group = self.environment()

        car = (
            Car()
            .shift(LEFT * 2)
            .move_to(all_items_group[0].get_start() + RIGHT * 5 + UP * 3)
        )

        self.add_dynamic_body(car.shovel, density=0.2)
        self.add_dynamic_body(car.body, density=5)
        self.add_dynamic_body(car.back_wheel, car.front_wheel, density=2, friction=0.8)
        self.add_shapes_filter(
            car.body, car.back_wheel, car.front_wheel, car.shovel, group=123
        )
        self.add_constraints(*car.add_constraints(static_body=all_items_group[0]))

        self.collision_detection(car, all_items_group[1:])
        self.camera.frame.move_to(car)

        self.camera.frame.add_updater(lambda m: m.move_to(car))

        # self.draw_debug_img(xlim=(-200, 200), ylim=(-1, 50))

        # UI
        title = Text("This is a Demo for manim-pymunk!", color=YELLOW, font_size=38)
        title.add_updater(lambda m: m.move_to(car.get_center() + DOWN * 4))
        self.add(title)

        self.wait(8)

    def collision_detection(self, car, all_items_group):
        COLLISION_TYPE = 123
        self.vspace._set_collision_type(car.shovel, COLLISION_TYPE)
        self.vspace._set_collision_type(car.body, COLLISION_TYPE)
        self.vspace._set_collision_type(car.front_wheel, COLLISION_TYPE)
        self.vspace._set_collision_type(car.back_wheel, COLLISION_TYPE)

        for item in all_items_group:
            self.vspace._set_collision_type(item, COLLISION_TYPE)

        def post_solve_callback(arbiter, space, data):
            impulse = arbiter.total_impulse
            strength = impulse.length
            if strength > 0.1:
                self.add_sound(
                    ASSETS_DIR / "click.wav",
                    gain=random.random(),
                )
            return True

        self.vspace._collision_detection_handler(
            collision_type_a=COLLISION_TYPE,
            collision_type_b=COLLISION_TYPE,
            post_solve=post_solve_callback,
        )

    def environment(self):

        all_items_group = Group()

        with Image.open(ASSETS_DIR / "dark_forast.png") as img:
            resized_img = img.resize(
                (config["pixel_width"], config["pixel_height"]),
                Image.Resampling.LANCZOS,
            )
            rgba_img = resized_img.convert("RGBA")
            pixel_array = np.array(rgba_img)
        self.camera.set_background(pixel_array)

        # items
        floor = VMobjectFromSVGPath(
            se.Path(
                "M0 11C0 7.3 0 3.7 0 0 27.3 0 54.7 0 82 0 78 0 77 1 72 3 68 4 68 3 64 2 60 4 57 2 51 1 43 2 40 4 38 6 34 11 31 6 26 6 20 5 15 7 11 10 8 11 4 11 0 11"
            )
        )
        floor.set_stroke(color=WHITE, width=10).set_fill(
            color=BLACK, opacity=0.8
        ).to_edge(DOWN, buff=0.1).scale(4)
        all_items_group.add(floor)

        # text
        text_str = "ILOVEUHELLOFUCKUMANHaHaHa"
        for t in text_str:
            text = Text(f"{t}", font_size=128 * random.random(), color=WHITE)
            text.move_to(
                floor.get_start()
                + UP * 10 * random.random()
                + RIGHT * 12 * random.random()
            )
            all_items_group.add(text)

        slope_anchors = floor.get_anchors()
        stone_radius = 0.4
        for i in range(0, len(slope_anchors)):
            dot = Dot(slope_anchors[i], color=RED, radius=stone_radius)
            dot.shift(UP * stone_radius)
            all_items_group.add(dot)

        x_min = floor.get_left()[0]
        x_max = floor.get_right()[0]
        y_min = floor.get_top()[1] + 10
        y_max = floor.get_top()[1] + 15

        rock_template = Apple(color=YELLOW, fill_opacity=1, fill_color=YELLOW)

        for _ in range(100):
            rand_x = random.uniform(x_min, x_max)
            rand_y = random.uniform(y_min, y_max)
            new_rock = rock_template.copy().scale(random.random() + 0.2)
            new_rock.move_to([rand_x, rand_y, 0])
            new_rock.rotate(random.uniform(0, PI * 0.25))
            all_items_group.add(new_rock)

        img_names = [
            "ak47.png",
            "awm.png",
            "football.png",
            "trislof.png",
        ] + ["bullts.png"] * 20

        for name in img_names:
            img = ImageMobject(ASSETS_DIR / name)
            rand_x = random.uniform(x_min, x_max)
            rand_y = random.uniform(y_min, y_max)
            img.move_to([rand_x, rand_y, 0])
            img.rotate(random.uniform(0, PI * 0.25))
            img.scale(random.random())
            all_items_group.add(img)

        self.add_static_body(floor)
        self.add_dynamic_body(*all_items_group[1:])
        return all_items_group
