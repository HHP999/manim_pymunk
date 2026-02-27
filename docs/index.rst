Welcome to Manim Pymunk Documentation
=======================================

**Manim Pymunk** is a project that integrates the Pymunk physics engine with the Manim animation library.

Project Features
----------------

This project provides the following core capabilities:

* **Physics Simulation Integration** - Seamlessly integrates the Pymunk 2D physics engine into the Manim animation framework, supporting rigid body dynamics, collision detection, and more.

* **Visual Constraints** - Provides Manim visualizations for various physical constraints, including:
  
  - PinJoint, SlideJoint, PivotJoint
  - GrooveJoint, RotaryLimitJoint
  - DampedSpring, DampedRotarySpring
  - GearJoint, RatchetJoint
  - SimpleMotor

* **Automatic Shape Generation** - Intelligently generates Pymunk collision shapes from Manim geometric objects, supporting:
  
  - Basic primitives like circles, lines, and polygons
  - Automatic subdivision sampling for complex curves
  - Automatic convex decomposition for non-convex shapes
  - Collision shape extraction from image pixel data

* **Real-time Synchronization** - Physics simulation results are automatically synced to Manim visual objects, featuring:
  
  - Real-time updates of rigid body position and rotation
  - Visualization of constraint forces
  - Multi-substep physics integration for enhanced stability

* **Flexible Configuration** - Comprehensive physical property interfaces, including:
  
  - Mass, moment of inertia, velocity, and angular velocity
  - Elasticity, friction, and collision types
  - Collision detection callbacks and filtering

* **Under the Hood** - The logic is quite straightforward—essentially a "wrapper" around Pymunk:

  - ``SpaceScene`` inherits from ``ZoomedScene``. Considering camera movement, it is better to wrap all functionalities directly.
  - Each ``Mobject`` calls an internal updater.
  - Properties like ``body``, ``shapes``, and ``angle`` (initialized to 0, as pinpoint accuracy isn't always critical) are attached directly to the ``Mobject`` via ``mob.set(body=body)``.
  - ``shapes`` include solid (polygons), hollow (segments), and images (using contour masks). Complex shapes are decomposed into multiple convex polygons and grouped.
  - You are free to modify or add attributes using the standard Pymunk API; this project simply simplifies the creation of shapes (the core part).

* **Usage Notes** - Please use the following template for your workflow:

  - Pymunk only supports 2D, so this is strictly for 2D physics animations.
  - Create Mobjects, set layouts, and configure styles (initialization).
  - Add Mobjects to one of the three body types: ``add_dynamic_body``, ``add_kinematic_body``, or ``add_static_body`` (this attaches and initializes the body, shapes, and angle).
  - Add shape filters (grouping objects that shouldn't collide) via ``add_shape_filter``.
  - Create constraints and use ``add_constraints_body`` to add them to the space.
  - Set up callback functions (for collision detection).
  - Start the animation!
  - Since my bandwidth is limited, many Pymunk APIs aren't fully wrapped. You can directly access the space via ``self.vspace.space``, or manipulate attributes via ``mob.body``, ``mob.shapes``, and ``mob.angle``.
  - Love you all!

* **Source Code** - This project is developed with AI assistance. Several features are still in progress:

  - The project structure may require refactoring.
  - Some APIs might be redundant or less than ergonomic.

API Reference
-------------

.. autosummary::
   :toctree: generated
   :recursive:
   :caption: API Reference:

   manim_pymunk

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`