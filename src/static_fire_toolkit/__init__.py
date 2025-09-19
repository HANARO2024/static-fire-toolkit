"""Static-Fire Toolkit core package."""

__all__ = ["__version__"]

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("static-fire-toolkit")  # pyproject의 project.name
except PackageNotFoundError:  # editable 설치 등 특수 상황 대비
    __version__ = "0+unknown"
