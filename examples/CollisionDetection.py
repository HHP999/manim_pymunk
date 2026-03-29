import random
from manim import *
from manim_pymunk import *


class VSpaceExample(SpaceScene):
    def construct(self):
        COLLISION_TYPE = 123
        # 1. 地板
        floor = Line(start=LEFT * 5, end=RIGHT * 5, stroke_width=12, color=BLUE)
        floor.to_edge(DOWN, buff=0.1)
        self.add_static_body(floor)

        # 2. 生成石头
        stone_num = 15
        stones = [
            Dot(color=BLUE).move_to(
                random.uniform(1, 3) * UP + random.uniform(-2, 2) * RIGHT
            )
            for _ in range(stone_num)
        ]
        self.add_dynamic_body(*stones)

        self.set_collision_type(floor, *stones, collision_type=COLLISION_TYPE)

        def post_solve_callback(arbiter, space, data):
            # 测试获取碰撞瞬间的冲量长度
            if arbiter.total_impulse.length > 0.2:
                print(f"Impact Strength: {arbiter.total_impulse.length:.2f}")
            return True

        self.set_collision_detection_handler(
            collision_type_a=COLLISION_TYPE,
            collision_type_b=COLLISION_TYPE,
            post_solve=post_solve_callback,
        )

        self.apply_impulse_at_local_point(*stones, impulse=(0, 0.1, 0))

        self.apply_force_at_world_point(stones[0], force=(0.1, 0, 0))

        start_pt = (0, 2, 0)
        end_pt = (0, -7, 0)
        self.add(Line(start_pt, end_pt, color=RED))

        self.wait(1.5)

        results = self.get_line_query(floor, start_pt, end_pt, stroke_width=0.1)

        if results:
            hit_point = results[0][2]  # 获取碰撞点坐标
            print(f"Floor detected at: {hit_point}")
            # 在探测到的位置画一个临时的红圈验证
            self.add(Dot(hit_point, color=YELLOW, radius=0.1))

        final_vel = self.get_velocity_at_local_point(stones[-1])
        print(f"Last stone velocity: {final_vel}")
        self.wait(1)
