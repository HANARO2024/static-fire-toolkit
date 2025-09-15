"""Style utilities for matplotlib defaults used by HANARO SFT.

This module applies the packaged mplstyle as default, while allowing
callers to override with an explicit style path.
"""

from __future__ import annotations

from importlib import resources

import matplotlib.pyplot as plt


def apply_default_style(style_path: str | None = None) -> None:
    """Apply the default HANARO matplotlib style.

    If ``style_path`` is provided, use that path. Otherwise, load the packaged
    ``hanaro_standard_stylesheet.mplstyle`` resource.
    """
    try:
        if style_path:
            plt.style.use(style_path)
            return

        style_file = resources.files("static_fire_toolkit").joinpath(
            "hanaro_standard_stylesheet.mplstyle"
        )
        plt.style.use(style_file.as_posix())
    except Exception:
        # Fallback to matplotlib defaults if style application fails.
        # We intentionally swallow exceptions to avoid breaking analysis
        # when the style file is missing or incompatible.
        return
