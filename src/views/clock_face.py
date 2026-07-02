"""Reusable geometry helpers for the analog clock face.

This file contains the low-level geometry that the view depends on.
Keeping the circle math here prevents the view module from turning into one
large block of mixed layout code and coordinate code.
"""

from __future__ import annotations

import math

import flet as ft
import flet.canvas as cv


def point_on_circle(
    center_x: float,
    center_y: float,
    radius: float,
    angle_degrees: float,
) -> tuple[float, float]:
    """Return a point on the dial.

    The subtraction by 90 degrees moves 0 degrees from the 3 o'clock axis to
    the 12 o'clock axis, which is the natural way people read a clock.
    """
    angle_radians = math.radians(angle_degrees - 90)
    return (
        center_x + radius * math.cos(angle_radians),
        center_y + radius * math.sin(angle_radians),
    )


def build_static_face_shapes(diameter: float) -> list[object]:
    """Create the shapes that rarely change: rings and tick marks."""
    center = diameter / 2
    outer_radius = diameter * 0.485
    inner_radius = diameter * 0.455
    marker_color = "#F8E8B5"
    subtle_marker = "#BDAE84"

    shapes: list[object] = [
        cv.Circle(
            x=center,
            y=center,
            radius=outer_radius,
            paint=ft.Paint(color="#000000", style=ft.PaintingStyle.FILL),
        ),
        cv.Circle(
            x=center,
            y=center,
            radius=diameter * 0.44,
            paint=ft.Paint(color="#050505", style=ft.PaintingStyle.FILL),
        ),
        cv.Circle(
            x=center,
            y=center,
            radius=outer_radius,
            paint=ft.Paint(color="#A89256", stroke_width=diameter * 0.008, style=ft.PaintingStyle.STROKE),
        ),
        cv.Circle(
            x=center,
            y=center,
            radius=inner_radius,
            paint=ft.Paint(color="#655531", stroke_width=diameter * 0.0035, style=ft.PaintingStyle.STROKE),
        ),
    ]

    for minute in range(60):
        is_hour_marker = minute % 5 == 0
        marker_length = diameter * (0.05 if is_hour_marker else 0.024)
        stroke_width = diameter * (0.008 if is_hour_marker else 0.003)
        marker_radius = outer_radius - diameter * 0.018
        start = point_on_circle(center, center, marker_radius - marker_length, minute * 6)
        end = point_on_circle(center, center, marker_radius, minute * 6)
        shapes.append(
            cv.Line(
                x1=start[0],
                y1=start[1],
                x2=end[0],
                y2=end[1],
                paint=ft.Paint(
                    color=marker_color if is_hour_marker else subtle_marker,
                    stroke_width=stroke_width,
                ),
            )
        )

    return shapes


def create_hand_shapes(diameter: float) -> list[object]:
    """Create the reusable canvas shapes for the moving hands.

    Performance note:
    these shapes are created once and then mutated in place every frame.
    That is cheaper than allocating a new list of new shapes for each update.
    """
    center = diameter / 2

    return [
        cv.Line(
            x1=center,
            y1=center,
            x2=center,
            y2=center,
            paint=ft.Paint(color="#F7E8B2", stroke_width=diameter * 0.016),
        ),
        cv.Line(
            x1=center,
            y1=center,
            x2=center,
            y2=center,
            paint=ft.Paint(color="#F1DD98", stroke_width=diameter * 0.011),
        ),
        cv.Line(
            x1=center,
            y1=center,
            x2=center,
            y2=center,
            paint=ft.Paint(color="#E7D8A5", stroke_width=diameter * 0.0035),
        ),
        cv.Circle(
            x=center,
            y=center,
            radius=diameter * 0.028,
            paint=ft.Paint(color="#E8DBAB", style=ft.PaintingStyle.FILL),
        ),
        cv.Circle(
            x=center,
            y=center,
            radius=diameter * 0.015,
            paint=ft.Paint(color="#7D6540", style=ft.PaintingStyle.FILL),
        ),
    ]


def update_hand_shapes(
    shapes: list[object],
    diameter: float,
    hour_angle: float,
    minute_angle: float,
    second_angle: float,
) -> None:
    """Mutate existing hand shapes in place for the next frame.

    The shapes list is expected to come from ``create_hand_shapes()``:
    index 0 = hour hand line,
    index 1 = minute hand line,
    index 2 = second hand line,
    index 3 = outer hub circle,
    index 4 = inner hub circle.
    """
    center = diameter / 2
    hour_end = point_on_circle(center, center, diameter * 0.21, hour_angle)
    minute_end = point_on_circle(center, center, diameter * 0.30, minute_angle)
    second_tail = point_on_circle(center, center, diameter * 0.11, second_angle + 180)
    second_tip = point_on_circle(center, center, diameter * 0.385, second_angle)

    hour_line = shapes[0]
    minute_line = shapes[1]
    second_line = shapes[2]

    if isinstance(hour_line, cv.Line):
        hour_line.x1 = center
        hour_line.y1 = center
        hour_line.x2 = hour_end[0]
        hour_line.y2 = hour_end[1]

    if isinstance(minute_line, cv.Line):
        minute_line.x1 = center
        minute_line.y1 = center
        minute_line.x2 = minute_end[0]
        minute_line.y2 = minute_end[1]

    if isinstance(second_line, cv.Line):
        second_line.x1 = second_tail[0]
        second_line.y1 = second_tail[1]
        second_line.x2 = second_tip[0]
        second_line.y2 = second_tip[1]


def numeral_specs(diameter: float) -> list[tuple[str, float, float, float]]:
    """Return label text, left, top, and font size for each numeral."""
    center = diameter / 2
    numeral_radius = diameter * 0.37
    font_size = diameter * 0.075
    specs: list[tuple[str, float, float, float]] = []

    for hour in range(1, 13):
        x, y = point_on_circle(center, center, numeral_radius, hour * 30)
        specs.append((str(hour), x, y, font_size))

    return specs


def badge_placeholder_bounds(diameter: float) -> tuple[float, float, float, float]:
    """Reserved area for the future badge image."""
    width = diameter * 0.209
    height = diameter * 0.209
    left = (diameter - width) / 2
    top = diameter * 0.195
    return left, top, width, height


def flag_placeholder_bounds(diameter: float) -> tuple[float, float, float, float]:
    """Reserved area for the future flag image."""
    width = diameter * 0.228
    height = diameter * 0.1425
    left = (diameter - width) / 2
    top = diameter * 0.70
    return left, top, width, height
