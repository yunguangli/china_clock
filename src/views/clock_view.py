"""Flet view for the analog clock.

This is the "view" part of MVC.

The view owns presentation details only:
* which controls exist,
* where they are placed,
* how they look,
* which layers appear above other layers.

The view does not decide what time it is and does not run the refresh loop.
It simply receives a ``ClockState`` and renders it.
"""

from __future__ import annotations

import flet as ft
import flet.canvas as cv

from models.clock_model import ClockState
from views.clock_face import (
    badge_placeholder_bounds,
    build_static_face_shapes,
    create_hand_shapes,
    flag_placeholder_bounds,
    numeral_specs,
    update_hand_shapes,
)


class AnalogClockView:
    """Render a decorative analog clock with learner-friendly structure."""

    def __init__(self, diameter: float = 680) -> None:
        self._diameter = diameter
        self._is_live = False
        self._last_state: ClockState | None = None
        self._hand_shapes: list[object] = []

        self._face_background = ft.Container()
        self._static_canvas = cv.Canvas()
        self._hands_canvas = cv.Canvas()
        self._title_label = ft.Text(
            value="中华人民共和国",
            color="#E9D9A3",
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            font_family="Georgia",
        )
        self._digital_label = ft.Text(
            value="00:00:00",
            color="#F5E8B7",
            text_align=ft.TextAlign.CENTER,
            font_family="Georgia",
        )
        self._date_label = ft.Text(
            value="",
            color="#C9B88C",
            text_align=ft.TextAlign.CENTER,
            font_family="Georgia",
        )
        self._badge_placeholder = ft.Container()
        self._flag_placeholder = ft.Container()
        self._stack = ft.Stack()
        self._numeral_controls: list[ft.Text] = []
        for numeral, x, y, font_size in numeral_specs(self._diameter):
            numeral_width = font_size * (1.35 if len(numeral) == 1 else 2.2)
            self._numeral_controls.append(
                ft.Text(
                    value=numeral,
                    left=x - numeral_width / 2,
                    top=y - font_size * 0.52,
                    width=numeral_width,
                    text_align=ft.TextAlign.CENTER,
                    size=font_size,
                    color="#FFF4C8",
                    weight=ft.FontWeight.BOLD,
                    font_family="Georgia",
                )
            )

        self._root = ft.Container(
            alignment=ft.Alignment.CENTER,
            content=self._stack,
        )

        self._rebuild_layout()

    @property
    def control(self) -> ft.Control:
        """Expose the root control to the composition root in main.py."""
        return self._root

    def mount(self) -> None:
        """Tell the view it can start pushing live updates to Flet."""
        self._is_live = True

    def unmount(self) -> None:
        """Tell the view to stop pushing live updates."""
        self._is_live = False

    def resize(self, diameter: float) -> None:
        """Resize the whole dial while keeping proportions intact."""
        new_diameter = max(320.0, min(860.0, float(diameter)))
        if abs(new_diameter - self._diameter) < 1:
            return

        self._diameter = new_diameter
        self._rebuild_layout()

        if self._last_state is not None:
            self.render(self._last_state)

    def render(self, state: ClockState) -> None:
        """Render one clock state.

        This method is intentionally narrow: the controller sends one state
        object, and the view translates it into UI changes.

        Performance note:
        only the moving-hand canvas is updated every frame. The larger root
        container is not repainted on every tick because that would be slower.
        """
        self._last_state = state
        time_changed = self._digital_label.value != state.digital_time
        date_changed = self._date_label.value != state.date_text

        if time_changed:
            self._digital_label.value = state.digital_time
        if date_changed:
            self._date_label.value = state.date_text

        update_hand_shapes(
            self._hand_shapes,
            diameter=self._diameter,
            hour_angle=state.hour_angle,
            minute_angle=state.minute_angle,
            second_angle=state.second_angle,
        )

        if self._is_live:
            self._hands_canvas.update()
            if time_changed:
                self._digital_label.update()
            if date_changed:
                self._date_label.update()

    def _rebuild_layout(self) -> None:
        """Recompute sizes and positions when the dial size changes.

        This method is intentionally heavier than ``render()`` and is called
        only when layout actually changes, such as during a resize.
        """
        diameter = self._diameter
        center = diameter / 2

        self._root.width = diameter
        self._root.height = diameter
        self._stack.width = diameter
        self._stack.height = diameter

        self._face_background.width = diameter
        self._face_background.height = diameter
        self._face_background.border_radius = ft.BorderRadius.all(diameter / 2)
        self._face_background.bgcolor = "#000000"
        self._face_background.border = ft.Border.all(diameter * 0.006, "#8F7A47")
        self._face_background.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=diameter * 0.05,
            color="#000000",
        )

        self._static_canvas.width = diameter
        self._static_canvas.height = diameter
        self._static_canvas.shapes = build_static_face_shapes(diameter)

        self._hands_canvas.width = diameter
        self._hands_canvas.height = diameter
        self._hand_shapes = create_hand_shapes(diameter)
        self._hands_canvas.shapes = self._hand_shapes

        self._title_label.size = diameter * 0.036
        self._title_label.width = diameter * 0.52
        self._title_label.left = center - self._title_label.width / 2
        self._title_label.top = diameter * 0.55

        self._digital_label.size = diameter * 0.042
        self._digital_label.width = diameter * 0.44
        self._digital_label.left = center - self._digital_label.width / 2
        self._digital_label.top = diameter * 0.605

        self._date_label.size = diameter * 0.024
        self._date_label.width = diameter * 0.58
        self._date_label.left = center - self._date_label.width / 2
        self._date_label.top = diameter * 0.652

        badge_left, badge_top, badge_width, badge_height = badge_placeholder_bounds(diameter)
        self._badge_placeholder.left = badge_left
        self._badge_placeholder.top = badge_top
        self._badge_placeholder.width = badge_width
        self._badge_placeholder.height = badge_height
        self._badge_placeholder.border_radius = ft.BorderRadius.all(diameter * 0.03)
        self._badge_placeholder.border = None
        self._badge_placeholder.bgcolor = "#000000"
        self._badge_placeholder.image = ft.DecorationImage(
            src="badge.png",
            fit=ft.BoxFit.CONTAIN,
        )
        self._badge_placeholder.opacity = 1.0

        flag_left, flag_top, flag_width, flag_height = flag_placeholder_bounds(diameter)
        self._flag_placeholder.left = flag_left
        self._flag_placeholder.top = flag_top
        self._flag_placeholder.width = flag_width
        self._flag_placeholder.height = flag_height
        self._flag_placeholder.border_radius = ft.BorderRadius.all(diameter * 0.012)
        self._flag_placeholder.border = None
        self._flag_placeholder.bgcolor = "#000000"
        self._flag_placeholder.image = ft.DecorationImage(
            src="flag.png",
            fit=ft.BoxFit.CONTAIN,
        )
        self._flag_placeholder.opacity = 1.0

        for i, (numeral, x, y, font_size) in enumerate(numeral_specs(diameter)):
            numeral_width = font_size * (1.35 if len(numeral) == 1 else 2.2)
            ctrl = self._numeral_controls[i]
            ctrl.left = x - numeral_width / 2
            ctrl.top = y - font_size * 0.52
            ctrl.width = numeral_width
            ctrl.size = font_size

        self._stack.controls = [
            self._face_background,
            self._static_canvas,
            self._badge_placeholder,
            *self._numeral_controls,
            self._flag_placeholder,
            self._hands_canvas,
            self._title_label,
            self._digital_label,
            self._date_label,
        ]
