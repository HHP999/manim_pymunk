import random
from manim import *
from manim_pymunk import *

class SpaceSceneExample(SpaceScene):
    def construct(self):

        COLLISION_TYPE = 123
        floor = Line(start=LEFT * 2, end=RIGHT * 10, stroke_width=12, color=RED)
        floor.to_edge(DOWN, buff=0.1)
        self.add_static_body(floor)
        self.vspace._set_collision_type(floor, COLLISION_TYPE)

        stone_num = 40

        stone_temp = Dot(ORIGIN, color=BLUE)
        for _ in range(stone_num):
            stone = stone_temp.copy().move_to(
                random.randint(1, 6) * UP + random.randint(-4, 4) * RIGHT
            )
            self.add_dynamic_body(stone)
            self.vspace._set_collision_type(stone, COLLISION_TYPE)

        def post_solve_callback(arbiter, space, data):
            # 1. 获取总冲量向量
            impulse = arbiter.total_impulse
            strength = impulse.length
            print(strength)
            if strength > 0.1:
                self.add_sound(
                    "D:/CoreKSetsManimPymunk/manim_pymunk/examples/assets/click.wav",
                )
            return True

        self.vspace._collision_detection_handler(
            collision_type_a=COLLISION_TYPE,
            collision_type_b=COLLISION_TYPE,
            post_solve=post_solve_callback,
        )

        self.wait(3)
