"""Tests for AirClass command edge triggering."""

from airclass.command_gate import CommandGate
from airclass.gesture_types import CommandName


def test_none_to_clear_passes_clear() -> None:
    gate = CommandGate()

    assert gate.gate(CommandName.CLEAR) is CommandName.CLEAR


def test_clear_held_repeatedly_returns_none_after_first_frame() -> None:
    gate = CommandGate()

    assert gate.gate(CommandName.CLEAR) is CommandName.CLEAR
    assert gate.gate(CommandName.CLEAR) is CommandName.NONE
    assert gate.gate(CommandName.CLEAR) is CommandName.NONE


def test_clear_can_fire_again_after_leaving_and_reentering() -> None:
    gate = CommandGate()

    assert gate.gate(CommandName.CLEAR) is CommandName.CLEAR
    assert gate.gate(CommandName.NONE) is CommandName.NONE
    assert gate.gate(CommandName.CLEAR) is CommandName.CLEAR


def test_none_to_next_slide_passes_next_slide() -> None:
    gate = CommandGate()

    assert gate.gate(CommandName.NEXT_SLIDE) is CommandName.NEXT_SLIDE


def test_next_slide_held_repeatedly_returns_none_after_first_frame() -> None:
    gate = CommandGate()

    assert gate.gate(CommandName.NEXT_SLIDE) is CommandName.NEXT_SLIDE
    assert gate.gate(CommandName.NEXT_SLIDE) is CommandName.NONE
    assert gate.gate(CommandName.NEXT_SLIDE) is CommandName.NONE


def test_previous_slide_held_repeatedly_returns_none_after_first_frame() -> None:
    gate = CommandGate()

    assert gate.gate(CommandName.PREVIOUS_SLIDE) is CommandName.PREVIOUS_SLIDE
    assert gate.gate(CommandName.PREVIOUS_SLIDE) is CommandName.NONE
    assert gate.gate(CommandName.PREVIOUS_SLIDE) is CommandName.NONE


def test_draw_remains_continuous() -> None:
    gate = CommandGate()

    assert gate.gate(CommandName.DRAW) is CommandName.DRAW
    assert gate.gate(CommandName.DRAW) is CommandName.DRAW


def test_pointer_remains_continuous() -> None:
    gate = CommandGate()

    assert gate.gate(CommandName.POINTER) is CommandName.POINTER
    assert gate.gate(CommandName.POINTER) is CommandName.POINTER


def test_none_remains_none() -> None:
    gate = CommandGate()

    assert gate.gate(CommandName.NONE) is CommandName.NONE
    assert gate.gate(CommandName.NONE) is CommandName.NONE
