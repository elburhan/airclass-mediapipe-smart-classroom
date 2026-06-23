"""Tests for the internal AirClass slide deck."""

import pytest

from airclass.slide_deck import Slide, SlideDeck, create_default_deck


def test_default_deck_has_at_least_four_slides() -> None:
    """The built-in demo deck should contain a useful number of slides."""
    deck = create_default_deck()
    assert deck.total_slides >= 4


def test_next_slide_advances_index() -> None:
    """next_slide should advance the deck when possible."""
    deck = SlideDeck((Slide("One"), Slide("Two")))

    assert deck.current_index == 0
    assert deck.next_slide() is True
    assert deck.current_index == 1
    assert deck.display_index == 2


def test_previous_slide_decreases_index() -> None:
    """previous_slide should move the deck backward when possible."""
    deck = SlideDeck((Slide("One"), Slide("Two")))
    deck.next_slide()

    assert deck.previous_slide() is True
    assert deck.current_index == 0


def test_cannot_move_before_first_slide() -> None:
    """The deck should not move before index zero."""
    deck = SlideDeck((Slide("One"), Slide("Two")))

    assert deck.previous_slide() is False
    assert deck.current_index == 0


def test_cannot_move_after_last_slide() -> None:
    """The deck should not move past the last slide."""
    deck = SlideDeck((Slide("One"), Slide("Two")))
    deck.next_slide()

    assert deck.next_slide() is False
    assert deck.current_index == 1


def test_slide_deck_rejects_empty_input() -> None:
    """A slide deck needs at least one slide."""
    with pytest.raises(ValueError, match="at least one slide"):
        SlideDeck(())
