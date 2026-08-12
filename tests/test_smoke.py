def test_core_importable():
    import core
    import core.operations  # noqa: F401 - import side effects (group registration)
