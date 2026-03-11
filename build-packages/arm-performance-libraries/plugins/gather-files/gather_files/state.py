from __future__ import annotations

from functools import wraps
from typing import Literal, TypedDict, Callable

from gather_files import GatherArmPerformanceLibraries

STATE = Literal["fetching", "fetched", "preparing", "prepared", "done", "failed"]


class StateMachineType(TypedDict):
    states: set[STATE | None]
    transitions: dict[STATE | None, set[STATE]]


STATE_MACHINE: StateMachineType = {
    "states": {"fetching", "fetched", "preparing", "prepared", "done", None},
    "transitions": {
        None: {"fetching"},
        "fetching": {"fetched"},
        "fetched": {"preparing"},
        "preparing": {"prepared"},
        "prepared": {"done"},
        "done": set(),
        "failed": {"fetching", "preparing"},
    },
}


def state_change(start: STATE, finished: STATE):
    if start not in STATE_MACHINE["states"]:
        raise ValueError(f"{start=} is not a valid state")
    if finished not in STATE_MACHINE["states"]:
        raise ValueError(f"{finished=} is not a valid state")
    if finished not in STATE_MACHINE["transitions"][start]:
        raise ValueError(f"{finished=} is not a valid transition for {start=}")

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self: GatherArmPerformanceLibraries, *args, **kwargs):
            state = self.state
            if start in STATE_MACHINE["transitions"][state] or state == start:
                self.state = start
                try:
                    func(self, *args, **kwargs)
                except Exception as e:
                    self.state = "failed"
                    raise e
                self.state = finished
            else:
                self.app.display_info(f"Skipping {func.__name__}; already done")

        return wrapper

    return decorator
