"""Internal AirClass slide deck simulation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Slide:
    """A single slide in the internal AirClass deck."""

    title: str
    subtitle: str | None = None
    bullets: tuple[str, ...] = ()


class SlideDeck:
    """A pure, bounded slide deck for the classroom demo."""

    def __init__(self, slides: tuple[Slide, ...] | list[Slide]) -> None:
        if not slides:
            raise ValueError("SlideDeck requires at least one slide.")
        self._slides: tuple[Slide, ...] = tuple(slides)
        self._current_index = 0

    @property
    def current_index(self) -> int:
        """Return the zero-based index of the current slide."""
        return self._current_index

    @property
    def current_slide(self) -> Slide:
        """Return the currently selected slide."""
        return self._slides[self._current_index]

    @property
    def total_slides(self) -> int:
        """Return the total number of slides in the deck."""
        return len(self._slides)

    @property
    def display_index(self) -> int:
        """Return the one-based slide index for UI display."""
        return self._current_index + 1

    def next_slide(self) -> bool:
        """Advance to the next slide when possible."""
        if self._current_index >= len(self._slides) - 1:
            return False
        self._current_index += 1
        return True

    def previous_slide(self) -> bool:
        """Move back to the previous slide when possible."""
        if self._current_index <= 0:
            return False
        self._current_index -= 1
        return True


def create_default_deck() -> SlideDeck:
    """Create the built-in AirClass demo deck."""
    return SlideDeck(
        (
            Slide(
                title="AirClass",
                subtitle="Touchless Classroom Control System",
                bullets=(
                    "A laptop-first classroom demo built around webcam gestures",
                    "Designed for a clean, readable presentation workflow",
                    "Keeps the interaction model self-contained and testable",
                ),
            ),
            Slide(
                title="Why Touchless Control Matters",
                subtitle="Fewer clicks, more focus",
                bullets=(
                    "Keep attention on the board instead of the keyboard",
                    "Reduce friction when presenting from across the room",
                    "Support quick navigation without touching the device",
                ),
            ),
            Slide(
                title="MediaPipe + OpenCV Pipeline",
                subtitle="Simple live vision loop",
                bullets=(
                    "Webcam frames are captured by OpenCV",
                    "Hand landmarks are detected by MediaPipe Hands",
                    "Gestures are recognized from normalized landmark data",
                ),
            ),
            Slide(
                title="Gesture to Command Mapping",
                subtitle="Recognition is separate from action",
                bullets=(
                    "Swipe Right maps to NEXT_SLIDE",
                    "Swipe Left maps to PREVIOUS_SLIDE",
                    "Pinch, Point, and Open Palm are displayed but not executed yet",
                ),
            ),
            Slide(
                title="Offline Demo Readiness",
                subtitle="Safe to present without network access",
                bullets=(
                    "Uses a local MediaPipe model file under assets/models/",
                    "Supports an offline readiness check before class",
                    "Keeps the classroom demo self-contained and reliable",
                ),
            ),
        )
    )
