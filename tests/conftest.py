"""Общие фикстуры pytest."""
import pytest

from app.core.deps import require_admin, require_auth
from main import app
from app.models import User

# Заглушка для legacy-интеграционных тестов, которым не нужна реальная авторизация.
_stub_user = User(
    id=999999,
    username="legacy_test_user",
    role="admin",
    is_active=True,
    request_limit=None,
)


def _stub_user_dep():
    return _stub_user


@pytest.fixture(autouse=True)
def _legacy_auth_bypass():
    """По умолчанию отключает авторизацию; auth-тесты снимают её самостоятельно."""
    app.dependency_overrides[require_auth] = _stub_user_dep
    app.dependency_overrides[require_admin] = _stub_user_dep
    yield
    app.dependency_overrides.clear()
