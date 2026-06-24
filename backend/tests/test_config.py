from app.core.config import Settings, _optional_port


def test_optional_port_accepts_empty_value() -> None:
    assert _optional_port(None) is None
    assert _optional_port("") is None
    assert _optional_port("1433") == 1433


def test_database_url_does_not_force_port() -> None:
    settings = Settings(
        db_server="CFR-I7-1",
        db_port=None,
        db_name="SBO_MEDINET_MIGRACION",
        db_user="test_user",
        db_password="test_password",
    )

    assert settings.database_url.host == "CFR-I7-1"
    assert settings.database_url.port is None
