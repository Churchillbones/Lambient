from core.config import config_service


def test_env_loading_and_base_dir(tmp_path, monkeypatch):
    # override BASE_DIR env var temporarily
    monkeypatch.setenv("BASE_DIR", str(tmp_path / "app_data"))

    # Reload settings
    from importlib import reload
    from core import config as config_pkg  # type: ignore
    reload(config_pkg)

    cfg = config_pkg.config_service
    base_dir = cfg.get("base_dir")

    assert base_dir.exists() and base_dir.is_dir()

    assert cfg.validate_configuration() is True 