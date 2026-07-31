import tomllib
from pathlib import Path


def test_no_forbidden_detector_dependencies() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    deps = " ".join(pyproject["project"]["dependencies"]).lower()
    assert "pupil-apriltags" not in deps


def test_required_scientific_constants() -> None:
    text = Path("configs/project.yaml").read_text(encoding="utf-8")
    assert "tag36h11" in text
    assert "tag_size_m: 0.020" in text
    assert "bending: 1.430" in text
    assert "torsion: 3.103" in text


def test_source_does_not_use_cv2_aruco() -> None:
    for path in Path("src").rglob("*.py"):
        assert "cv2.aruco" not in path.read_text(encoding="utf-8")
