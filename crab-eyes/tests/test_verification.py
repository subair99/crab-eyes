import pytest

from app.gate.dates import after_cutoff


def test_no_cutoff_keeps_everything():
    assert not after_cutoff(None, None)
    assert not after_cutoff("2026-01-01", None)


def test_source_after_cutoff_is_rejected():
    assert after_cutoff("2025-04-10", "2025-04-09")


def test_source_on_cutoff_is_kept():
    assert not after_cutoff("2025-04-09", "2025-04-09")


def test_undated_source_is_rejected_when_cutoff_set():
    assert after_cutoff(None, "2025-04-09")


def test_datetime_strings_are_accepted():
    assert not after_cutoff("2025-03-01T10:00:00Z", "2025-04-09")


def test_bad_cutoff_raises():
    with pytest.raises(ValueError):
        after_cutoff("2025-01-01", "April 9")
