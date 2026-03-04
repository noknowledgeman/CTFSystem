import os
import sys

import pytest


def main() -> int:
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    return pytest.main(["-vv"])


if __name__ == "__main__":
    raise SystemExit(main())

