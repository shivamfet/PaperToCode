import pytest
from main import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset slowapi rate limiter state between tests."""
    limiter.reset()
    yield
    limiter.reset()
