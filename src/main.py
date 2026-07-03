"""Analog clock application entry point.

Architecture overview
---------------------
This project uses a small Model-View-Controller split so each file has one
clear job:

1. ``models.clock_model.ClockModel``
    Owns time state and converts the current ``datetime`` into hand angles.
    The model is pure Python logic, so learners can understand the clock math
    without first learning Flet widgets.

2. ``views.clock_view.AnalogClockView``
    Owns presentation only. It builds the visible clock face, images, title,
    numerals, and the canvas layer used to draw the hands. The view receives a
    ready-made state object and turns that state into pixels.

3. ``controllers.clock_controller.ClockController``
    Owns the update loop. It asks the model for a fresh snapshot many times per
    second and tells the view to render that snapshot. This keeps timing logic
    out of the view.

How MVC works together at runtime
---------------------------------
The three layers cooperate in a loop:

1. ``main()`` creates one model, one view, and one controller.
2. ``main()`` gives the view's root control to Flet so it can appear on the page.
3. The controller starts an ``asyncio`` task.
4. That task repeatedly asks the model for a ``ClockState`` snapshot.
5. The controller passes that snapshot to the view.
6. The view updates only the controls that need repainting.

This separation matters because each layer can change independently:

* you can change the dial design without touching time math,
* you can change the hand-angle math without touching the UI layout,
* you can change refresh timing without rewriting either of the other two.

What each Flet control is doing
-------------------------------
The clock is made from a small set of Flet primitives:

* ``ft.Page`` is the application window and top-level surface.
* ``ft.SafeArea`` keeps content away from unsafe screen edges on devices that
    have system bars or cutouts.
* ``ft.Container`` is used for the circular face background, for centering,
    and for holding the badge and flag images.
* ``ft.Stack`` layers controls in painter's order, which is what makes it easy
    to place the static dial, images, numerals, and moving hands on top of one
    another.
* ``ft.Text`` draws the numerals, title text, digital time, and date label.
* ``flet.canvas.Canvas`` is used twice:
    one canvas for static artwork such as rings and scale marks, and one canvas
    for dynamic artwork such as the moving hands.
* ``ft.DecorationImage`` places the badge and flag inside containers while
    keeping their layout independent from the rest of the face.

Why two canvas layers are used
------------------------------
The clock face is split into a static canvas and a dynamic canvas for
performance reasons.

* The static canvas contains artwork that rarely changes: rings and scale marks.
* The dynamic canvas contains only the hands, which change every frame.

If everything were redrawn on one canvas every update, the app would do more
work than needed. Splitting the layers reduces unnecessary repainting and keeps
the code easier to reason about.

How the clock is built
----------------------
The analog clock is drawn from layered Flet controls inside a ``ft.Stack``.
Earlier controls are painted first and later controls appear on top.

1. The background face is a circular container.
2. A static canvas draws the rings and minute/hour scale marks.
3. Text controls place the numbers 1 to 12 around the dial.
4. Badge and flag images are positioned as ordinary controls.
5. A second canvas draws the moving hands above the face artwork.

How the numbers and scale work
------------------------------
The helper code in ``views.clock_face`` uses circle math to place items around
the dial. A point on the dial is computed from:

* the center of the clock,
* a radius from that center,
* an angle in degrees.

The code subtracts 90 degrees before converting to radians. That shifts the
mathematical zero-angle direction from 3 o'clock to 12 o'clock, which matches
how people read clocks.

The 12 numerals are placed every 30 degrees because:

* a full circle is 360 degrees,
* 12 hours share that circle,
* so each hour mark is ``360 / 12 = 30`` degrees apart.

The minute scale uses 60 marks, so each mark is ``360 / 60 = 6`` degrees apart.
Every fifth minute mark is drawn longer and thicker so it doubles as an hour
marker.

How the hands are drawn
-----------------------
The hands are lines drawn on a canvas from the center of the dial to an end
point calculated from angle and length.

* The hour hand is shorter and thicker.
* The minute hand is longer and slightly thinner.
* The second hand is the thinnest and also has a small tail behind the center.

This is simpler than rotating image assets because a line can be redrawn at the
exact angle needed for every frame.

How the hands move - triggers, event flow, and rendering
--------------------------------------------------------
The clock hands are animated by an asyncio task running at 60 Hz (16.67 ms per
frame). Here is the complete event flow for each frame:

Trigger:
--------
The *only* trigger is time - specifically ``asyncio.sleep(1/60)`` in the
controller's ``_run()`` loop. No user input, no Flet events, no OS timers.
This is a deliberate design: a clock is a time-driven system, not an
event-driven one.

Event flow (per frame):
-----------------------
1. **Controller** (``ClockController._run``):
   - Wakes up every ~16.67 ms (60 Hz).
   - Checks ``page.visible`` - if the app is minimized/backgrounded, it skips
     the frame to save CPU.
   - Calls ``model.snapshot(now)`` to get a fresh ``ClockState``.

2. **Model** (``ClockModel.snapshot``):
   - Captures ``datetime.now(UTC_PLUS_8)``.
   - Computes three angles with sub-second precision:
     * ``second_angle = (seconds + microseconds/1e6) * 6``   (6 deg/sec)
     * ``minute_angle = (minutes + second_progress/60) * 6`` (6 deg/min)
     * ``hour_angle   = ((hour%12) + minute_progress/60) * 30`` (30 deg/hour)
   - Formats digital time (``%H:%M:%S``) and date (``%A, %d %B %Y``).
   - Returns immutable ``ClockState`` dataclass.

3. **Controller → View** (``view.render(state)``):
   - Passes the ``ClockState`` snapshot to the view. No events, no callbacks,
     just a plain data object.

4. **View** (``AnalogClockView.render``):
   - Updates ``_digital_label.value`` and ``_date_label.value`` *only if text
     changed* (avoids redundant Flet updates).
   - Calls ``update_hand_shapes()`` which **mutates** the existing canvas
     shapes in place:
     * ``hour_line.x2, y2`` ← new endpoint from ``hour_angle``
     * ``minute_line.x2, y2`` ← new endpoint from ``minute_angle``
     * ``second_line.x1,y1,x2,y2`` ← tail + tip from ``second_angle``
   - Calls ``_hands_canvas.update()`` - **only the hands canvas repaints**.
   - Conditionally calls ``_digital_label.update()`` / ``_date_label.update()``.

Key performance points:
-----------------------
* **No layout rebuild** - ``_rebuild_layout()`` runs only on window resize.
* **No root update** - ``_root.update()`` is never called in the render loop.
* **Mutable canvas shapes** - ``create_hand_shapes()`` allocates once;
  ``update_hand_shapes()`` mutates coordinates in place.
* **Two canvases** - Static face (rings, ticks) on one canvas; moving hands on
  another. Only the hands canvas repaints at 60 Hz.
* **Visibility gating** - Controller skips work when page is not visible.

Why 60 Hz?
----------
At 60 Hz the second hand moves every frame (6° per frame = smooth sweep).
At 30 Hz it would move 12° per frame - visibly jittery. The cost is ~2x more
``canvas.update()`` calls, which is negligible on modern hardware.

Why not Flet's ``page.on_timer`` or ``ft.Timer``?
-------------------------------------------------
``asyncio`` gives precise, drift-free timing and integrates with Flet's own
event loop. ``asyncio.sleep`` yields to Flet so the UI stays responsive.
"""

import asyncio

import flet as ft

from controllers.clock_controller import ClockController
from models.clock_model import ClockModel
from views.clock_view import AnalogClockView


def _preferred_diameter(page: ft.Page) -> float:
    """Pick a dial size that stays readable across window sizes."""
    page_width = float(page.width or 0)
    page_height = float(page.height or 0)

    if page_width <= 0:
        page_width = float(getattr(page.window, "width", 900) or 900)
    if page_height <= 0:
        page_height = float(getattr(page.window, "height", 980) or 980)

    return min(page_width - 60, page_height - 100, 820)


def main(page: ft.Page) -> None:
    """Compose the model, controller, and view for the analog clock app."""
    page.title = "Analog Clock"
    page.bgcolor = "#000000"
    page.padding = 0
    page.window.width = 960
    page.window.height = 1040
    page.window.resizable = True
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    model = ClockModel()
    view = AnalogClockView(diameter=700)
    controller = ClockController(model=model, view=view, refresh_hz=60.0)

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=view.control,
            ),
        )
    )

    view.mount()
    page.update()
    view.resize(_preferred_diameter(page))

    _resize_task: asyncio.Task[None] | None = None

    async def _debounced_resize() -> None:
        try:
            await asyncio.sleep(0.1)
            view.resize(_preferred_diameter(page))
        except asyncio.CancelledError:
            pass

    async def on_resized(e: ft.ControlEvent) -> None:
        nonlocal _resize_task
        if _resize_task is not None:
            _resize_task.cancel()
        _resize_task = asyncio.create_task(_debounced_resize())

    page.on_resized = on_resized
    controller.start()

    async def on_close(e) -> None:
        await controller.stop()
        view.unmount()

    page.on_close = on_close


ft.run(main)
