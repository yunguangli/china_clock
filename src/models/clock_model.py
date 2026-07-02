"""Time model for the analog clock.

This is the "model" part of MVC.

Why this file exists:
* it isolates time and angle math from drawing code,
* it makes the logic easier to test,
* it lets learners understand the clock rules without UI noise.

The model does not know anything about Flet controls, pages, canvases, or
layout. It only knows how to turn the current time into a snapshot of values
that a view can render.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


# Fixed timezone for HK/Beijing time (UTC+8), independent of host settings.
UTC_PLUS_8 = timezone(timedelta(hours=8), name="UTC+08:00")


@dataclass(frozen=True)
class ClockState:
    """Snapshot of everything the view needs to render one frame.

    A frozen dataclass is useful here because it acts like a read-only message
    passed from the model to the view through the controller.
    """

    current_time: datetime
    hour_angle: float
    minute_angle: float
    second_angle: float
    digital_time: str
    date_text: str


class ClockModel:
    """Keeps the current time and converts it into hand angles.

    Angles are measured in degrees, clockwise, with 0 degrees pointing to 12.
    That convention is easy to explain and lets the view focus only on drawing.

    In MVC terms, this class answers the question:
    "What should the clock show right now?"
    """

    def __init__(self) -> None:
        self._current_time: datetime | None = None

    @property
    def current_time(self) -> datetime | None:
        """Expose the latest captured time for debugging or testing."""
        return self._current_time

    def snapshot(self, now: datetime | None = None) -> ClockState:
        """Capture the current time and derive the angles for all hands.

        The fractional calculations are what make the analog motion look smooth:
        the second hand uses microseconds, the minute hand borrows progress from
        seconds, and the hour hand borrows progress from minutes.
        """
        # Always use a fixed UTC+8 wall clock so the app shows HK/Beijing time
        # no matter where the program is running.
        current_time = now or datetime.now(UTC_PLUS_8)
        self._current_time = current_time

        # Include fractions so the hands move continuously instead of stepping.
        second_progress = current_time.second + current_time.microsecond / 1_000_000
        minute_progress = current_time.minute + second_progress / 60
        hour_progress = (current_time.hour % 12) + minute_progress / 60

        return ClockState(
            current_time=current_time,
            hour_angle=hour_progress * 30,
            minute_angle=minute_progress * 6,
            second_angle=second_progress * 6,
            digital_time=current_time.strftime("%H:%M:%S"),
            date_text=current_time.strftime("%A, %d %B %Y"),
        )
