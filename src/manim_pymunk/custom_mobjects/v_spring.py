import numpy as np
from manim import *

class VSpring(Line):
    def __init__(
        self,
        start=LEFT,
        end=RIGHT,
        turns=18,
        amplitude=0.1,
        end_length=0.2,
        stroke_width=1,
        color=WHITE,
        **kwargs
    ):
        self.turns = turns
        self.amplitude = amplitude
        self.end_length = end_length
        # 注意：Line 内部会调用 generate_points()
        super().__init__(start, end, stroke_width=stroke_width, color=color, **kwargs)

    def generate_points(self):
        """重写 generate_points，使其不再生成直线，而是生成螺旋线"""
        # 1. 计算当前起点和终点的距离
        start = self._pointify(self.start)
        end = self._pointify(self.end)
        vec = end - start
        total_dist = np.linalg.norm(vec)
        
        # 避免除零错误
        if total_dist < 0.001:
            self.set_points_as_corners([start, end])
            return

        # 2. 在水平方向（x轴）生成螺旋点集
        helix_dist = max(total_dist - 2 * self.end_length, 0.01)
        points = []

        # 起始端子
        points.append([0, 0, 0])
        points.append([self.end_length, 0, 0])

        # 螺旋部分
        num_steps = self.turns * 12
        for i in range(num_steps + 1):
            t = i / num_steps
            angle = 2 * PI * self.turns * t
            x = self.end_length + t * helix_dist
            
            # 渐收系数，确保与端子水平衔接
            taper = 1.0
            if t < 0.1: taper = t / 0.1
            elif t > 0.9: taper = (1 - t) / 0.1
            
            y = self.amplitude * np.sin(angle) * taper
            points.append([x, y, 0])

        # 结束端子
        points.append([self.end_length + helix_dist + self.end_length, 0, 0])

        # 3. 将生成的水平点集应用变换，对齐到 start -> end 向量
        self.set_points_as_corners(points)
        self.make_smooth() # 产生平滑的螺旋效果
        
        # 旋转和平移
        target_angle = angle_of_vector(vec)
        self.rotate(target_angle, about_point=ORIGIN)
        self.shift(start)

    def put_start_and_end_on(self, start, end):
        """当位置改变时（如被 Updater 调用），重新生成点"""
        self.start = np.array(start)
        self.end = np.array(end)
        self.generate_points()
        return self