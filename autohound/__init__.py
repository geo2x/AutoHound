# AutoHound © 2026 Gordon Prescott

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("autohound")
except PackageNotFoundError:
    __version__ = "1.0.3"  # fallback for editable installs
__author__ = "Gordon Prescott"
__copyright__ = "Copyright (c) 2026 Gordon Prescott. All rights reserved."

from autohound import models

__all__ = ["models", "__version__", "__author__", "__copyright__"]
