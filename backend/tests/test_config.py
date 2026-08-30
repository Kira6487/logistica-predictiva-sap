from app.core.config import Settings, _optional_port
import pytest


def test_optional_port_accepts_empty_value() -> None:
    assert _optional_port(None) is None
    assert _optional_port("") is None
    assert _optional_port("1433") == 1433


def test_database_url_does_not_force_port() -> None:
    settings = Settings(
        db_server="demo.example.invalid",
        db_port=None,
        db_name="demo_database",
        db_user="test_user",
        db_password="test_password",
    )

    assert settings.database_url.host == "demo.example.invalid"
    assert settings.database_url.port is None


def test_database_url_requires_encryption_and_certificate_validation() -> None:
    settings = Settings(
        db_server="demo.example.invalid",
        db_port=1433,
        db_name="demo_database",
        db_user="reader",
        db_password="local-test-secret",
        db_encrypt="yes",
        db_trust_server_certificate="no",
    )

    assert settings.database_url.query["Encrypt"] == "yes"
    assert settings.database_url.query["TrustServerCertificate"] == "no"


def test_database_url_rejects_missing_password() -> None:
    with pytest.raises(ValueError, match="DB_PASSWORD"):
        Settings(db_password="").database_url
