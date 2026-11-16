"""``python -m orgbrain.benchmarks`` entry point — delegates to the runner CLI."""

from __future__ import annotations

from orgbrain.benchmarks.runner import main

if __name__ == "__main__":
    raise SystemExit(main())
