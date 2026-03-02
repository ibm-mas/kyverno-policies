import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--namespace",
        action="store",
        default=None,
        help="Kubernetes namespace to test policies in"
    )

@pytest.fixture
def namespace(request):
    return request.config.getoption("--namespace")
