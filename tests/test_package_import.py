"""Verify the installed distribution resolves its intended source package."""

from importlib import import_module
from importlib.metadata import distribution
from pathlib import Path


def test_installed_package_import() -> None:
    package = import_module("video_freshness_lab")
    metadata = distribution("video-freshness-lab")
    expected = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "video_freshness_lab"
        / "__init__.py"
    )

    assert package.__file__ is not None
    assert Path(package.__file__).resolve() == expected, (
        "Expected this checkout's editable installation; run pip install -e '.[dev]'"
    )
    assert metadata.metadata["Name"] == "video-freshness-lab"
    assert not metadata.requires or all(
        "extra ==" in requirement for requirement in metadata.requires
    ), "The foundation must not acquire runtime dependencies"
