"""Regression: cli.main must not silently return 2 for a missing dispatch branch."""

from __future__ import annotations

import argparse

import pytest

from pyrtkai.cli import main


def test_main_raises_runtime_error_when_subcommand_not_dispatched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ns = argparse.Namespace(cmd="__missing_dispatch_test__")

    def fake_parse(self: argparse.ArgumentParser, argv: list[str] | None = None) -> argparse.Namespace:
        return ns

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", fake_parse)
    with pytest.raises(RuntimeError, match="unhandled pyrtkai subcommand"):
        main([])
