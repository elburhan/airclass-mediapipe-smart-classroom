"""Tests for the internal AirClass action executor."""

from airclass.action_executor import ActionExecutor
from airclass.gesture_types import CommandName
from airclass.slide_deck import Slide, SlideDeck


class _FakeClock:
    """Deterministic clock for cooldown tests."""

    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


def _deck() -> SlideDeck:
    """Create a small deck for execution tests."""
    return SlideDeck((Slide("One"), Slide("Two")))


def test_pointer_with_position_updates_pointer_state() -> None:
    """POINTER should update the pointer position when available."""
    executor = ActionExecutor(_deck())

    result = executor.execute(CommandName.POINTER, position=(0.25, 0.75))

    assert result.executed is True
    assert result.state.pointer_position == (0.25, 0.75)
    assert result.state.status_message == "Pointer active."


def test_pointer_without_position_does_not_crash() -> None:
    """POINTER should fail gracefully when no position is provided."""
    executor = ActionExecutor(_deck())

    result = executor.execute(CommandName.POINTER)

    assert result.executed is False
    assert result.state.pointer_position is None
    assert "unavailable" in result.message.lower()


def test_draw_appends_drawing_points() -> None:
    """DRAW should append points to the persistent drawing overlay."""
    executor = ActionExecutor(
        _deck(),
        drawing_max_jump_distance=1.0,
    )

    first = executor.execute(CommandName.DRAW, position=(0.10, 0.20))
    second = executor.execute(CommandName.DRAW, position=(0.30, 0.40))

    assert first.executed is True
    assert second.executed is True
    assert second.state.drawing_points == ((0.10, 0.20), (0.30, 0.40))
    assert second.state.drawing_strokes == (((0.10, 0.20), (0.30, 0.40)),)
    assert second.state.drawing_points_added == 2
    assert second.state.status_message == "Drawing."


def test_draw_ignores_jittery_points_too_close_together() -> None:
    """DRAW should skip points that are too close to the last point."""
    executor = ActionExecutor(
        _deck(),
        drawing_min_point_distance=0.05,
        drawing_max_jump_distance=1.0,
    )

    executor.execute(CommandName.DRAW, position=(0.10, 0.20))
    result = executor.execute(CommandName.DRAW, position=(0.12, 0.21))

    assert result.state.drawing_points == ((0.10, 0.20),)


def test_draw_appends_points_when_movement_is_large_enough() -> None:
    """DRAW should add points when the fingertip moves enough."""
    executor = ActionExecutor(
        _deck(),
        drawing_min_point_distance=0.05,
        drawing_max_jump_distance=1.0,
    )

    executor.execute(CommandName.DRAW, position=(0.10, 0.20))
    result = executor.execute(CommandName.DRAW, position=(0.20, 0.30))

    assert result.state.drawing_points == ((0.10, 0.20), (0.20, 0.30))


def test_draw_history_is_capped() -> None:
    """Drawing history should stay bounded."""
    executor = ActionExecutor(
        _deck(),
        max_drawing_points=3,
        drawing_max_jump_distance=1.0,
    )

    executor.execute(CommandName.DRAW, position=(0.10, 0.20))
    executor.execute(CommandName.DRAW, position=(0.20, 0.30))
    executor.execute(CommandName.DRAW, position=(0.30, 0.40))
    result = executor.execute(CommandName.DRAW, position=(0.40, 0.50))

    assert result.state.drawing_points == (
        (0.20, 0.30),
        (0.30, 0.40),
        (0.40, 0.50),
    )


def test_clear_empties_drawing_points_and_pointer() -> None:
    """CLEAR should reset the board-local visual state."""
    executor = ActionExecutor(_deck())
    executor.execute(CommandName.POINTER, position=(0.25, 0.75))
    executor.execute(CommandName.DRAW, position=(0.10, 0.20))

    result = executor.execute(CommandName.CLEAR)

    assert result.executed is True
    assert result.state.pointer_position is None
    assert result.state.drawing_points == ()
    assert result.state.drawing_strokes == ()
    assert result.state.drawing_resets == 1
    assert result.state.status_message == "Drawing cleared."


def test_repeated_clear_commands_are_rate_limited() -> None:
    """Holding an open palm should not execute CLEAR on every frame."""
    clock = _FakeClock()
    executor = ActionExecutor(
        _deck(),
        clear_command_cooldown_seconds=1.0,
        clock=clock,
    )

    first = executor.execute(CommandName.CLEAR)
    repeated = executor.execute(CommandName.CLEAR)
    clock.value = 1.0
    after_cooldown = executor.execute(CommandName.CLEAR)

    assert first.executed is True
    assert repeated.executed is False
    assert "cooldown" in repeated.message.lower()
    assert after_cooldown.executed is True


def test_clear_executes_again_after_command_transition() -> None:
    """Returning to CLEAR should execute even within the hold cooldown."""
    clock = _FakeClock()
    executor = ActionExecutor(
        _deck(),
        clear_command_cooldown_seconds=1.0,
        clock=clock,
    )

    first = executor.execute(CommandName.CLEAR)
    executor.execute(CommandName.NONE)
    transitioned = executor.execute(CommandName.CLEAR)

    assert first.executed is True
    assert transitioned.executed is True


def test_none_does_not_add_drawing_points() -> None:
    """NONE should not add drawing points and should hide the pointer."""
    executor = ActionExecutor(_deck())
    executor.execute(CommandName.DRAW, position=(0.10, 0.20))
    executor.execute(CommandName.POINTER, position=(0.25, 0.75))

    result = executor.execute(CommandName.NONE)

    assert result.executed is False
    assert result.state.pointer_position is None
    assert result.state.drawing_points == ((0.10, 0.20),)
    assert result.state.status_message is None


def test_none_ends_stroke_without_erasing_drawing() -> None:
    """A later drawing attempt should begin a separate stroke."""
    executor = ActionExecutor(
        _deck(),
        drawing_max_jump_distance=1.0,
    )
    executor.execute(CommandName.DRAW, position=(0.10, 0.20))
    executor.execute(CommandName.NONE)

    result = executor.execute(CommandName.DRAW, position=(0.80, 0.70))

    assert result.state.drawing_strokes == (
        ((0.10, 0.20),),
        ((0.80, 0.70),),
    )


def test_large_jump_starts_separate_stroke() -> None:
    """A tracking jump should not create a long line across the board."""
    executor = ActionExecutor(
        _deck(),
        drawing_max_jump_distance=0.15,
    )
    executor.execute(CommandName.DRAW, position=(0.10, 0.20))

    result = executor.execute(CommandName.DRAW, position=(0.80, 0.70))

    assert result.state.drawing_strokes == (
        ((0.10, 0.20),),
        ((0.80, 0.70),),
    )


def test_draw_does_not_generate_intermediate_points() -> None:
    """Each accepted DRAW frame should add at most one point."""
    executor = ActionExecutor(
        _deck(),
        drawing_max_jump_distance=1.0,
    )
    executor.execute(CommandName.DRAW, position=(0.20, 0.30))

    result = executor.execute(CommandName.DRAW, position=(0.40, 0.30))

    assert result.state.drawing_points == ((0.20, 0.30), (0.40, 0.30))
    assert result.state.drawing_points_added == 2
    assert result.state.drawing_points[-1] == (0.40, 0.30)


def test_clear_resets_drawing_state_for_next_stroke() -> None:
    """The first point after CLEAR should begin a clean stroke."""
    executor = ActionExecutor(
        _deck(),
        drawing_max_jump_distance=1.0,
    )
    executor.execute(CommandName.DRAW, position=(0.10, 0.10))
    executor.execute(CommandName.CLEAR)

    result = executor.execute(CommandName.DRAW, position=(0.80, 0.80))

    assert result.state.drawing_strokes == (((0.80, 0.80),),)


def test_pointer_does_not_add_drawing_points() -> None:
    """POINTER must preserve drawing without appending to it."""
    executor = ActionExecutor(_deck())
    executor.execute(CommandName.DRAW, position=(0.10, 0.20))

    result = executor.execute(CommandName.POINTER, position=(0.70, 0.80))

    assert result.state.pointer_position == (0.70, 0.80)
    assert result.state.drawing_points == ((0.10, 0.20),)
    assert result.state.drawing_points_added == 1


def test_pointer_ends_active_drawing_stroke() -> None:
    """Returning to DRAW after POINTER should begin a separate stroke."""
    executor = ActionExecutor(_deck(), drawing_max_jump_distance=1.0)
    executor.execute(CommandName.DRAW, position=(0.10, 0.20))
    executor.execute(CommandName.POINTER, position=(0.50, 0.50))

    result = executor.execute(CommandName.DRAW, position=(0.20, 0.30))

    assert result.state.pointer_position is None
    assert result.state.drawing_strokes == (
        ((0.10, 0.20),),
        ((0.20, 0.30),),
    )


def test_slide_navigation_still_works() -> None:
    """Swipe-driven navigation should still move the internal deck."""
    clock = _FakeClock()
    executor = ActionExecutor(_deck(), slide_command_cooldown_seconds=0.0, clock=clock)

    next_result = executor.execute(CommandName.NEXT_SLIDE)
    prev_result = executor.execute(CommandName.PREVIOUS_SLIDE)

    assert next_result.executed is True
    assert next_result.slide_index == 2
    assert prev_result.executed is True
    assert prev_result.slide_index == 1


def test_next_slide_at_last_slide_does_not_exceed_bounds() -> None:
    """NEXT_SLIDE should not move beyond the last slide."""
    deck = _deck()
    deck.next_slide()
    executor = ActionExecutor(deck, slide_command_cooldown_seconds=0.0)

    result = executor.execute(CommandName.NEXT_SLIDE)

    assert result.executed is False
    assert result.slide_index == 2
    assert "last slide" in result.message.lower()


def test_previous_slide_at_first_slide_does_not_go_below_zero() -> None:
    """PREVIOUS_SLIDE should not move before the first slide."""
    executor = ActionExecutor(_deck(), slide_command_cooldown_seconds=0.0)

    result = executor.execute(CommandName.PREVIOUS_SLIDE)

    assert result.executed is False
    assert result.slide_index == 1
    assert "first slide" in result.message.lower()


def test_slide_navigation_cooldown_blocks_repeated_execution() -> None:
    """Repeated navigation commands should be rate-limited."""
    clock = _FakeClock()
    executor = ActionExecutor(_deck(), slide_command_cooldown_seconds=1.0, clock=clock)

    first = executor.execute(CommandName.NEXT_SLIDE)
    second = executor.execute(CommandName.NEXT_SLIDE)

    assert first.executed is True
    assert second.executed is False
    assert "cooldown" in second.message.lower()
