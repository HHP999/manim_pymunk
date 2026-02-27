# Manim Pymunk

**Manim Pymunk** is a project that integrates the Pymunk physics engine with the Manim animation library.

### Example Demo

<video src="https://github.com/HHP999/manim_pymunk/raw/master/examples/assets/example.mp4" width="600" controls muted autoplay loop>
  Your browser does not support video playback.
</video>

## Project Features

This project provides the following core functionalities:

### Physics Simulation Integration

Seamlessly integrates the Pymunk 2D physics engine into the Manim animation framework, supporting rigid body dynamics, collision detection, and other physical phenomena.

### Visualized Constraints

Provides Manim visual implementations for various physical constraints, including:

- **Positional Constraints**: PinJoint, SlideJoint, PivotJoint
- **Path Constraints**: GrooveJoint
- **Rotational Constraints**: RotaryLimitJoint
- **Spring Constraints**: DampedSpring, DampedRotarySpring
- **Transmission Constraints**: GearJoint, RatchetJoint, SimpleMotor

### Automatic Shape Generation

Intelligently generates Pymunk collision shapes from Manim geometric objects, supporting:

- Basic shapes such as Circles, Lines, and Polygons.
- Automatic subdivision sampling for complex curves.
- Automatic convex decomposition for non-convex shapes.
- Collision shape extraction from image pixel data.

### Real-time Synchronization

Physics simulation results are automatically synchronized to Manim visual objects, supporting:

- Real-time updates of rigid body position and rotation.
- Visual representation of constraint forces.
- Multi-stepping physical integration for improved stability.

### Flexible Configuration

A complete interface for physical property configuration, including:

- velocity, angular velocity, etc.
- Shape elasticity, friction, collision types, etc.
- Collision detection callbacks and collision filtering.

## Design Principles

The design principle of this project is straightforward—it wraps a "Manim skin" over Pymunk:

- **Architecture**: `SpaceScene` inherits from `ZoomedScene`. Considering camera movements, it currently encapsulates all features into a unified scene class.
- **Constraint System**: Every Mobject invokes an internal updater to synchronize physical states with visuals.
- **Property Management**: `body`, `shapes`, and `angle` are attached as Mobject attributes, initialized via `mob.set(body=body)`.
- **Shape Generation**:
  - **Solid Shapes**: Generates polygons directly.
  - **Hollow Shapes**: Constructs outlines using line segments.
  - **Image Shapes**: Extracts shapes using contour masks.
  - **Complex Shapes**: Decomposes non-convex shapes into multiple polygons.

> **Note**: The current version provides default initialization values for all properties. You can modify them directly as needed. The core goal of this project is to facilitate the rapid creation of collision shapes.

## Quick Start

### Basic Workflow

```python
from manim import *
from manim_pymunk import *


class VPivotJointExample(SpaceScene):
    def construct(self):
        # manim Mobject
        static_dot = Dot(ORIGIN)
        square = Square().move_to(static_dot)
        square2 = Square().move_to(static_dot.get_center() + UP * 2).scale(0.5)

        constraints = [
            VPivotJoint(static_dot, square),
            VPivotJoint(
                square,
                square2,
                pivot_world= UP*3,
            ),
        ]
        # add physics body shapes angle
        self.add_static_body(static_dot)
        self.add_dynamic_body(square, square2, angular_velocity=PI * 2)
        # add collision filter
        self.add_shapes_filter(static_dot, square, square2, group=2)
        # add constraints
        self.add_constraints(*constraints)
        # Start Physics Simulation , 
        # Note: Any animation will trigger physics simulation unless you manually remove the object from 
        # the physics controls or remove the SpaceScene updater.
        self.wait(3)

```
