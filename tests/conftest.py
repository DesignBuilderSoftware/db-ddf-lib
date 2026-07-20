from pathlib import Path

import pandas as pd
import pytest

from ddf_lib import CDT

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "samples"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def samples_dir() -> Path:
    return SAMPLES_DIR


@pytest.fixture
def construction_ddf_path() -> Path:
    return SAMPLES_DIR / "construction and materials.ddf"


@pytest.fixture
def glazing_ddf_path() -> Path:
    return SAMPLES_DIR / "glazing and shading.DDF"


@pytest.fixture
def simple_cdt_path() -> Path:
    """Small, hand-written CDT fixture file (read-only)."""
    return FIXTURES_DIR / "Simple.cdt"


@pytest.fixture
def simple_cdt() -> CDT:
    """In-memory CDT matching tests/fixtures/Simple.cdt."""
    df = pd.DataFrame(
        [
            ["1", "Brick", "0.84"],
            ["2", "Concrete Block", "1.63"],
            ["3", "Mineral Wool", "0.038"],
        ],
        columns=["Id", "Name", "Conductivity"],
    )
    return CDT(ids=[1, 2, 3], df=df)
