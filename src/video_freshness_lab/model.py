"""Immutable numbered evidence and strict integer-millisecond inputs."""

from dataclasses import dataclass, field


def integer(name: str, value: int, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


@dataclass(frozen=True, slots=True)
class Frame:
    session_id: int
    sequence: int
    produced_at_ms: int
    frame_id: str = field(init=False)

    def __post_init__(self) -> None:
        for name in ("session_id", "sequence", "produced_at_ms"):
            integer(name, getattr(self, name))
        object.__setattr__(
            self, "frame_id", f"epoch-{self.session_id}/frame-{self.sequence}"
        )
