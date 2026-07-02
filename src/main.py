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

How the hands move
------------------
The controller refreshes the clock about 30 times per second. On each refresh:

1. The model reads the current time.
2. It converts that time into angles.
3. The view redraws the hands with the new angles.

The model uses fractional progress so the hands move smoothly instead of
jumping:

* second angle = ``seconds + microseconds`` converted into 6 degrees per second,
* minute angle = ``minutes + second_progress / 60`` converted into 6 degrees,
* hour angle = ``(hour % 12) + minute_progress / 60`` converted into 30 degrees.

That is why the second hand sweeps and why the minute and hour hands creep
forward continuously instead of stepping once per unit.

Performance notes for learners
------------------------------
Flet control updates are convenient, but they are not free. A common beginner
mistake is calling ``update()`` on a large parent control too often.

This clock is designed to avoid that pattern:

* layout rebuilds happen only when the window size changes,
* the moving hands repaint on their own canvas,
* the digital time and date are updated only when their displayed text changes,
* the whole root container is not repainted every frame.

That strategy keeps the animation smooth while avoiding unnecessary work.
"""

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
    controller = ClockController(model=model, view=view, refresh_hz=30.0)

    # Render once before mounting so the page never flashes placeholder values.
    view.render(model.snapshot())

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

    def on_resized(e: ft.ControlEvent) -> None:
        view.resize(_preferred_diameter(page))

    page.on_resized = on_resized
    controller.start()


ft.run(main)
