# Manim Pymunk

**Manim Pymunk** 是一个将 Pymunk 物理引擎与 Manim 动画库集成的项目。

### 示例演示

<video src="https://github.com/HHP999/manim_pymunk/raw/master/examples/assets/example.mp4" width="600" controls muted autoplay loop>
  您的浏览器不支持视频播放。
</video>
## 项目特点

本项目提供了以下核心功能：

### 物理模拟集成

将 Pymunk 2D 物理引擎无缝集成到 Manim 动画框架中，支持刚体动力学、碰撞检测等物理现象的模拟。

### 可视化约束

提供多种物理约束的 Manim 可视化实现，包括：

- **位置约束**：固定关节 (PinJoint)、滑动关节 (SlideJoint)、枢轴关节 (PivotJoint)
- **轨道约束**：滑槽关节 (GrooveJoint)
- **旋转约束**：旋转限制 (RotaryLimitJoint)
- **弹簧约束**：阻尼弹簧 (DampedSpring)、阻尼旋转弹簧 (DampedRotarySpring)
- **传动约束**：齿轮约束 (GearJoint)、棘轮约束 (RatchetJoint)、电动机约束 (SimpleMotor)

### 自动形状生成

智能从 Manim 几何对象生成 Pymunk 碰撞形状，支持：

- 圆形、直线、多边形等基本图形
- 复杂曲线的自动细分采样
- 非凸形状的自动凸分解
- 图片像素数据的碰撞形状提取

### 实时同步

物理模拟结果自动同步到 Manim 视觉对象，支持：

- 刚体位置和旋转的实时更新
- 约束力的可视化表现
- 多子步物理积分提高稳定性

### 灵活配置

完整的物理属性配置接口，包括：

- 刚体质量、惯性矩、速度、角速度等
- 形状弹性、摩擦力、碰撞类型等
- 碰撞检测回调和碰撞过滤

## 设计原理

该项目的设计原理非常简单——在 Pymunk 上套了一层 Manim 的皮：

- **整体架构**：`SpaceScene` 继承 `ZoomedScene`，考虑到相机移动，目前采用直接包圆所有功能的方式
- **约束系统**：每个 Mobject 都在内部调用更新器，实现物理状态与视觉同步
- **属性管理**：`body`、`shapes`、`angle` 都挂在 Mobject 属性上，使用 `mob.set(body=body)` 方式初始化
- **形状生成**：
  - 实心形状：直接生成多边形
  - 空心形状：使用线段组成轮廓
  - 图片形状：使用轮廓蒙版提取
  - 复杂形状：使用凸分解为多个多边形

> **注意**：当前版本已经为所有属性提供了默认初始化值，您可以根据需要直接修改，项目的核心目标是方便快速创建碰撞形状。

## 快速开始

### 基本使用流程

```python
from manim import *
from manim_pymunk import SpaceScene, VSlideJoint
import pymunk

class PhysicsDemo(SpaceScene):
    def construct(self):
        # 1. 创建 Mobject 并进行布局、样式配置
        circle = Circle(fill_color=BLUE, fill_opacity=1)
        circle.scale(0.5)
  
        # 2. 将 Mobject 添加为动态刚体
        self.add_dynamic_body(circle)
  
        # 3. 添加到场景
        self.add(circle)
  
        # 4. 播放动画
        self.wait(3)
```

### 完整示例

```python
from manim import *
from manim_pymunk import SpaceScene, VPinJoint
import pymunk

class ConstraintDemo(SpaceScene):
    def construct(self):
        # 创建两个物体
        circle1 = Circle(radius=0.3, fill_color=BLUE, fill_opacity=1)
        circle2 = Circle(radius=0.3, fill_color=RED, fill_opacity=1)
  
        circle1.move_to(LEFT * 2)
        circle2.move_to(RIGHT * 2)
  
        # 添加为动态刚体
        self.add_dynamic_body(circle1)
        self.add_dynamic_body(circle2)
  
        # 创建固定关节约束
        pin_joint = VPinJoint(circle1, circle2, distance=2.0)
        self.add_constraints_body(pin_joint)
  
        # 添加到场景
        self.add(circle1, circle2, pin_joint)
  
        # 播放动画
        self.wait(5)
```

## 主要 API

### VSpace（物理空间管理）

```python
space = VSpace(gravity=(0, -9.81), sub_step=8)
space.init_updater()  # 启动物理模拟

# 配置刚体
space.set_body_angle_shape(mob, body_type=pymunk.Body.DYNAMIC, is_solid=True)

# 施加力
space.apply_force_at_world_point(mob, force=(10, 0), point=[0, 0, 0])

# 施加脉冲
space.apply_impulse_at_world_point(mob, impulse=(5, 5), point=[0, 0, 0])

# 坐标转换
world_pos = space.local_to_world(mob, point=[1, 0, 0])
local_pos = space.world_to_local(mob, point=[0, 0, 0])

# 碰撞检测
point_info = space.get_point_query_info(mob, point=[0, 0, 0])
line_info = space.get_line_query(mob, start=[0, 0, 0], end=[1, 1, 0], stroke_width=0.1)
```

### 约束类

所有约束类都继承自 `VConstraint`，使用统一接口：

```python
# 固定关节
pin_joint = VPinJoint(mob_a, mob_b, distance=2.0)

# 滑动关节
slide_joint = VSlideJoint(mob_a, mob_b, min_dist=0.5, max_dist=2.0)

# 弹簧约束
spring = VDampedSpring(mob_a, mob_b, rest_length=1.0, stiffness=100, damping=10)

# 齿轮约束
gear = VGearJoint(mob_a, mob_b, phase=0.0, ratio=1.0)
```

## 重要说明

### 当前限制

- **2D Only**：Pymunk 仅支持 2D 物理，因此本项目只能用于 2D 物理动画创作
- **API 覆盖**：当前版本未完全封装 Pymunk 的所有 API

### 扩展用法

对于未封装的 Pymunk API，您可以直接操作内部对象：

```python
# 直接访问 Pymunk Space
vspace.space.add(custom_constraint)

# 直接访问刚体属性
mob.body.velocity = (10, 0)
mob.body.angular_velocity = 2.0

# 直接访问形状属性
for shape in mob.shapes:
    shape.friction = 0.5
    shape.elasticity = 0.8
```

### 碰撞过滤

使用碰撞过滤器控制物体之间的碰撞检测：

```python
# 添加碰撞过滤器（设置分组）
space._add_shape_filter(mob_a, group=1, categories=1, mask=0xFFFFFFFE)
space._add_shape_filter(mob_b, group=2, categories=2, mask=0xFFFFFFFE)

# 注册碰撞回调
space._collision_detection_handler(
    collision_type_a=1,
    collision_type_b=2,
    begin=on_collision_begin,
    separate=on_collision_separate
)
```

## 项目状态

本项目使用 AI 辅助开发，目前还有多个功能未完成：

- [ ] 项目结构重构
- [ ] API 优化和简化
- [ ] 使用 `@dataclass` 整合参数
- [ ] 完整的 Pymunk API 封装
- [ ] 完整的使用示例库
- [ ] 详细的教程文档

## 安装

```bash
pip install manim pymunk
```

## 文档

详见 [`docs/`](./docs/) 目录中的完整 API 文档。

## 许可证

MIT License

---

**感谢使用 Manim Pymunk！** 🎬✨
