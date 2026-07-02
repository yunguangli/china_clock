"""Controller that keeps the clock view in sync with the model.

This is the "controller" part of MVC.

Its job is coordination, not drawing and not clock math:
* ask the model for fresh state,
* pass that state to the view,
* decide how often refreshes happen.
"""

from __future__ import annotations

import asyncio

from models.clock_model import ClockModel
from views.clock_view import AnalogClockView


class ClockController:
    """Run a small async loop that refreshes the view at a steady rate.

    This class is deliberately small. For a clock, the controller should be a
    thin timing layer rather than a second place where business logic accumulates.
    """

    def __init__(
        self,
        model: ClockModel,
        view: AnalogClockView,
        refresh_hz: float = 30.0,
    ) -> None:
        self._model = model
        self._view = view
        self._refresh_seconds = 1.0 / max(refresh_hz, 1.0)
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Start the refresh loop once.

        The loop is owned by the controller because time coordination belongs in
        the control layer, not in the view.
        """
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        """Continuously publish fresh model snapshots to the view.

        ``asyncio.sleep()`` yields control back to Flet's event loop so the UI
        remains responsive while the clock keeps moving.
        """
        while True:
            state = self._model.snapshot()
            self._view.render(state)
            await asyncio.sleep(self._refresh_seconds)
