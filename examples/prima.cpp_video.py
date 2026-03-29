from manim import *
from manim_pymunk import *
from pathlib import Path

# 获取资源目录
ASSETS_DIR = Path(__file__).parent / "assets"


class ImageMobjectTest(SpaceScene):
    def construct(self):
        title = Text("Prima.cpp")
        # 理论，前言探索
