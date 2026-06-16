from genshin_ai import __version__


def test_package_version_is_defined() -> None:
    assert __version__ == "0.1.0"


def test_package_can_be_imported() -> None:
    import genshin_ai

    assert genshin_ai is not None
