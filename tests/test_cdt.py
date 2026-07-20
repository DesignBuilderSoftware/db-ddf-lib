"""Unit tests for ddf_lib.schema.CDT (single CDT table parsing/writing)."""

import pandas as pd
import pytest

from ddf_lib import CDT
from ddf_lib.schema import SEPARATOR_DATA, SEPARATOR_HEADER


class TestParseLine:
    def test_header_line(self):
        assert CDT._parse_line("#4 #5 #6", SEPARATOR_HEADER) == ["4", "5", "6"]

    def test_data_line(self):
        assert CDT._parse_line("#1  #Brick  #0.84", SEPARATOR_DATA) == [
            "1",
            "Brick",
            "0.84",
        ]

    def test_values_containing_spaces_are_preserved(self):
        line = "#Id #Name #Mat 1 #Mat 2"
        assert CDT._parse_line(line, SEPARATOR_HEADER) == [
            "Id",
            "Name",
            "Mat 1",
            "Mat 2",
        ]

    def test_single_element_line(self):
        assert CDT._parse_line("#42", SEPARATOR_HEADER) == ["42"]


class TestRead:
    def test_read_fixture_file(self, simple_cdt_path, simple_cdt):
        cdt = CDT.read(str(simple_cdt_path))

        assert cdt is not None
        assert cdt.ids == [1, 2, 3]
        assert list(cdt.df.columns) == ["Id", "Name", "Conductivity"]
        assert cdt.df.shape == (3, 3)
        assert cdt.df.equals(simple_cdt.df)

    def test_read_preserves_values_as_strings(self, simple_cdt_path):
        cdt = CDT.read(str(simple_cdt_path))

        assert cdt.df.loc[0, "Conductivity"] == "0.84"
        assert cdt.df.loc[1, "Name"] == "Concrete Block"

    def test_read_missing_file_returns_none(self, tmp_path):
        assert CDT.read(str(tmp_path / "DoesNotExist.cdt")) is None

    def test_read_empty_file_returns_none(self, tmp_path):
        empty = tmp_path / "Empty.cdt"
        empty.write_text("")
        assert CDT.read(str(empty)) is None

    def test_read_malformed_file_returns_none(self, tmp_path):
        bad = tmp_path / "Bad.cdt"
        # Row length does not match the number of columns.
        bad.write_text("#1 #2\n#Id #Name\n#1  #a  #extra  #cols\n")
        assert CDT.read(str(bad)) is None

    def test_read_file_with_no_data_rows(self, tmp_path):
        headers_only = tmp_path / "HeadersOnly.cdt"
        headers_only.write_text("#1 #2\n#Id #Name\n")
        cdt = CDT.read(str(headers_only))

        assert cdt is not None
        assert cdt.ids == [1, 2]
        assert list(cdt.df.columns) == ["Id", "Name"]
        assert cdt.df.empty


class TestSave:
    def test_save_writes_expected_format(self, tmp_path, simple_cdt):
        out = tmp_path / "Out.cdt"
        simple_cdt.save(str(out))

        lines = out.read_text().splitlines()
        assert lines[0] == "#1 #2 #3"
        assert lines[1] == "#Id #Name #Conductivity"
        assert lines[2] == "#1  #Brick  #0.84"
        assert lines[4] == "#3  #Mineral Wool  #0.038"

    def test_save_matches_fixture_file(self, tmp_path, simple_cdt, simple_cdt_path):
        out = tmp_path / "Out.cdt"
        simple_cdt.save(str(out))

        assert out.read_text() == simple_cdt_path.read_text()

    def test_round_trip(self, tmp_path, simple_cdt):
        out = tmp_path / "RoundTrip.cdt"
        simple_cdt.save(str(out))
        reread = CDT.read(str(out))

        assert reread is not None
        assert reread.ids == simple_cdt.ids
        assert reread.df.equals(simple_cdt.df)

    def test_save_coerces_non_string_values(self, tmp_path):
        df = pd.DataFrame([[1, 2]], columns=["Id", "Value"])
        cdt = CDT(ids=[1], df=df)
        out = tmp_path / "Coerced.cdt"
        cdt.save(str(out))

        reread = CDT.read(str(out))
        assert reread.df.loc[0, "Id"] == "1"
        assert reread.df.loc[0, "Value"] == "2"
