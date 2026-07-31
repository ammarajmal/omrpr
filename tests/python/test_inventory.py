from pathlib import Path

from omrpr_analysis.inventory import sha256


def test_sha256(tmp_path: Path) -> None:
    path = tmp_path / "sample"
    path.write_bytes(b"abc")
    assert sha256(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
