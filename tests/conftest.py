# Seeking Pips | Enzo Nunez (enzonunez) | CS 2104, section 83521
# Honor code: As a Hokie, I will conduct myself with honor and integrity at
#   all times. I will not lie, cheat, or steal, nor will I accept the actions
#   of those who do.
# LLM use: I used Claude Code by Anthropic for code generation and debugging.

"""Shared pytest fixtures: a fresh app and database for every test."""
import sys
from pathlib import Path

import pytest

# The app lives in code/, which is not a package, so put it on the path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from app import create_app  # noqa: E402


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True,
                       "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()
