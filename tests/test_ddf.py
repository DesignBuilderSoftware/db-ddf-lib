"""Unit tests for ddf_lib.schema.DDF (zip container of CDT files)."""

from dataclasses import fields
from zipfile import ZipFile

import pandas as pd

from ddf_lib import CDT, DDF

ALL_FIELDS = [f.name for f in fields(DDF)]


def make_empty_ddf(**overrides) -> DDF:
    """Build a DDF with all attributes None except the given overrides."""
    kwargs = {name: None for name in ALL_FIELDS}
    kwargs.update(overrides)
    return DDF(**kwargs)


class TestRead:
    def test_read_construction_sample(self, construction_ddf_path):
        ddf = DDF.read(str(construction_ddf_path))

        assert ddf.available_attributes == ["Constructions", "Materials"]
        assert isinstance(ddf.Materials, CDT)
        assert isinstance(ddf.Constructions, CDT)
        assert ddf.Glazing is None

    def test_read_construction_sample_data(self, construction_ddf_path):
        ddf = DDF.read(str(construction_ddf_path))

        assert ddf.Materials.df.shape == (2, 111)
        assert list(ddf.Materials.df.columns[:2]) == ["Id", "Name"]
        assert ddf.Constructions.df.shape == (1, 176)
        assert all(isinstance(i, int) for i in ddf.Constructions.ids)

    def test_read_glazing_sample(self, glazing_ddf_path):
        ddf = DDF.read(str(glazing_ddf_path))

        assert ddf.available_attributes == [
            "Glazing",
            "InternalBlinds",
            "Panes",
            "WindowGas",
        ]
        assert ddf.Materials is None

    def test_read_missing_file_returns_all_none(self, tmp_path):
        ddf = DDF.read(str(tmp_path / "missing.ddf"))

        assert ddf.available_attributes == []
        assert all(getattr(ddf, name) is None for name in ALL_FIELDS)

    def test_read_non_zip_file_returns_all_none(self, tmp_path):
        bogus = tmp_path / "bogus.ddf"
        bogus.write_text("this is not a zip archive")
        ddf = DDF.read(str(bogus))

        assert ddf.available_attributes == []

    def test_read_ignores_unknown_cdt_files(self, tmp_path, simple_cdt_path, capsys):
        ddf_file = tmp_path / "unknown.ddf"
        with ZipFile(ddf_file, "w") as z:
            z.write(simple_cdt_path, "NotARealTable.cdt")

        ddf = DDF.read(str(ddf_file))

        assert ddf.available_attributes == []
        assert "NotARealTable" in capsys.readouterr().out


class TestAvailability:
    def test_available_attributes_and_has_data(self, simple_cdt):
        ddf = make_empty_ddf(Materials=simple_cdt)

        assert ddf.available_attributes == ["Materials"]
        assert ddf.has_data("Materials") is True
        assert ddf.has_data("Glazing") is False

    def test_has_data_unknown_attribute_is_false(self):
        ddf = make_empty_ddf()
        assert ddf.has_data("NoSuchAttribute") is False


class TestSave:
    def test_save_writes_only_populated_cdts(self, tmp_path, simple_cdt):
        ddf = make_empty_ddf(Materials=simple_cdt)
        out = tmp_path / "out.ddf"
        ddf.save(str(out))

        with ZipFile(out) as z:
            assert z.namelist() == ["Materials.cdt"]

    def test_round_trip_in_memory_ddf(self, tmp_path, simple_cdt):
        ddf = make_empty_ddf(Materials=simple_cdt)
        out = tmp_path / "round_trip.ddf"
        ddf.save(str(out))

        reread = DDF.read(str(out))
        assert reread.available_attributes == ["Materials"]
        assert reread.Materials.ids == simple_cdt.ids
        assert reread.Materials.df.equals(simple_cdt.df)

    def test_round_trip_sample_ddf(self, tmp_path, construction_ddf_path):
        original = DDF.read(str(construction_ddf_path))
        out = tmp_path / "resaved.ddf"
        original.save(str(out))

        reread = DDF.read(str(out))
        assert reread.available_attributes == original.available_attributes
        for name in original.available_attributes:
            assert getattr(reread, name).ids == getattr(original, name).ids
            pd.testing.assert_frame_equal(
                getattr(reread, name).df, getattr(original, name).df
            )

    def test_save_after_edit_round_trips_edit(self, tmp_path, construction_ddf_path):
        ddf = DDF.read(str(construction_ddf_path))
        ddf.Materials.df.loc[0, "Name"] = "MODIFIED_VALUE"
        out = tmp_path / "edited.ddf"
        ddf.save(str(out))

        reread = DDF.read(str(out))
        assert reread.Materials.df.loc[0, "Name"] == "MODIFIED_VALUE"
