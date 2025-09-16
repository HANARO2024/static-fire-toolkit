"""Package entry point for `python -m static_fire_toolkit`.

Delegates execution to `static_fire_toolkit.cli.main()`.
"""

from static_fire_toolkit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
