import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture()
def in_temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)
