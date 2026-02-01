
from pymunk import Space
from manim import VGroup,Mobject

class VConstraint(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __check_data(self):
        pass

    def install(self, space: Space):
        "安装更新器"
        pass

    def mob_updater(self, mob:Mobject, dt:float):
        "更新器"
        pass







