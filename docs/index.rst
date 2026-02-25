欢迎使用 Manim Pymunk 文档
===========================

**Manim Pymunk** 是一个将 Pymunk 物理引擎与 Manim 动画库集成的项目。

项目特点
--------

本项目提供了以下核心功能：

* **物理模拟集成** - 将Pymunk 2D物理引擎无缝集成到Manim动画框架中, 支持刚体动力学、碰撞检测等。

* **可视化约束** - 提供多种物理约束的Manim可视化实现, 包括：
  
  - 固定关节(PinJoint)、滑动关节(SlideJoint)、枢轴关节(PivotJoint)
  - 滑槽关节(GrooveJoint)、旋转限制(RotaryLimitJoint)
  - 弹簧约束(DampedSpring、DampedRotarySpring)
  - 齿轮约束(GearJoint)、棘轮约束(RatchetJoint)
  - 电动机约束(SimpleMotor)

* **自动形状生成** - 智能从Manim几何对象生成Pymunk碰撞形状, 支持：
  
  - 圆形、直线、多边形等基本图形
  - 复杂曲线的自动细分采样
  - 非凸形状的自动凸分解
  - 图片像素数据的碰撞形状提取

* **实时同步** - 物理模拟结果自动同步到Manim视觉对象, 支持：
  
  - 刚体位置和旋转的实时更新
  - 约束力的可视化表现
  - 多子步物理积分提高稳定性

* **灵活配置** - 完整的物理属性配置接口, 包括：
  
  - 刚体质量、惯性矩、速度、角速度等
  - 形状弹性、摩擦力、碰撞类型等
  - 碰撞检测回调和碰撞过滤

* **原理** - 原理非常简单,只是在pymunk上套了层皮:
   - SpaceScene 继承 ZoomedScene, 考虑到相机移动, 不如直接包圆所有功能
   - 每个Mobject都在内部调用更新器, 
   - body, shapes,angle(我全部初始化为0, 目前我认为不需要太较真)都挂在Mobject属性上, 使用mob.set(body=body)
   - shapes 有实心(多边形), 空心(线段), 图片(使用轮廓蒙版),复杂形状使用凸分解为多个多边形, 组合在一起即可
   - 你可以自由按照 pymunk的API修改属性, 添加属性, 本项目只是为了方便创建shapes(核心)
* **注意** - 你应该使用以下模板使用该库:
   - pymunk只支持2D,所以你只能用于2D物理动画创作
   - 创建 Mobject, 布局, 样式等配置(初始化)
   - 将Mobject 按需求加入三种body种类, (此处挂载body, shapes,angle, 并初始化)使用self.add_dynamic_body, self.add_kinematic_body, self.add_static_body
   - 添加碰撞过滤器(就是分组, 哪些物体之间不需要碰撞)add_shape_filter
   - 创建约束并使用 add_constraints_body 加入space
   - 回调函数(碰撞检测)
   - 开启动画
   - 由于我精力有限, 很多pymunk的API没有封装完, 所以你可以之间使用self.vspace.space操作空间, 以及mob.body,mob.shapes,mob.angle直接操作属性
   - 爱你们

* **项目源码** - 本项目使用AI辅助开发, 目前还有多个功能未完成：
   - 项目结构可能需要重构
   - 项目API可能冗余或者不方便
   - body, shapes等初始化属性暂时都写死了, 我想使用@dataclass整合参数, 然后传入Pymunk(未开始)

* **代码示例**
  ```python
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
      ```

API 参考
--------

.. autosummary::
   :toctree: generated
   :recursive:
   :caption: API Reference:

   manim_pymunk

索引
----

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

