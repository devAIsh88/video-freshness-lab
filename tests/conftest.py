"""Tests must leave no additional live threads in the pytest process."""

from threading import enumerate as enumerate_threads

import pytest


@pytest.fixture(autouse=True)
def no_background_thread_leaks():
    baseline = set(enumerate_threads())
    yield
    extras = [t.name for t in enumerate_threads() if t not in baseline]
    assert not extras, f"unexpected live threads after test: {extras}"
