import hashlib
import json
import zipfile

import pytest

from research.data import fetch, french_blocks, read_prices, verify_sources


def test_source_hash_mismatch_is_not_silently_accepted(tmp_path):
    path = tmp_path / "prices.csv"
    path.write_bytes(b"original")
    with pytest.raises(ValueError, match="revision"):
        fetch("https://example.invalid", path, "0" * 64)


def test_selected_french_return_block_rejects_schema_corruption(tmp_path):
    path = tmp_path / "momentum.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "table.csv", "Average Value Weighted Returns -- Monthly\n,A,B\n200001,1,2,3\n"
        )
    with pytest.raises(ValueError, match="Malformed"):
        french_blocks(path)


def test_unselected_metadata_does_not_relabel_a_corrupt_equal_weight_table(tmp_path):
    path = tmp_path / "momentum.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "table.csv",
            "Average Value Weighted Returns -- Monthly\n,A,B\n200001,1,2\n\n"
            "Average Equal Weighted Returns -- Monthly\n,A,B\n200001,1,2,3\n",
        )
    assert french_blocks(path)[0][1].shape == (1, 2)
    with pytest.raises(ValueError, match="Malformed"):
        french_blocks(path, "equal")


def test_price_only_csv_is_not_mislabeled_total_return(tmp_path):
    path = tmp_path / "asset.csv"
    path.write_text("Date,Close,Volume\n2000-01-03,100,1000\n")
    with pytest.raises(ValueError, match="Adjusted"):
        read_prices(path)


def test_every_experiment_refuses_changed_cached_data(tmp_path):
    (tmp_path / ".cache").mkdir()
    (tmp_path / "results").mkdir()
    data = b"fixed source vintage"
    source = tmp_path / ".cache/prices.csv"
    source.write_bytes(data)
    (tmp_path / "results/data_manifest.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "path": ".cache/prices.csv",
                        "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                ]
            }
        )
    )
    assert len(verify_sources(tmp_path)) == 64
    source.write_bytes(b"revised")
    with pytest.raises(ValueError, match="dataset changed"):
        verify_sources(tmp_path)
