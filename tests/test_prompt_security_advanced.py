import pytest
from enterpriseguard.security.prompt_security_advanced import PromptSecurityGuard, PromptAnalysisResult

@pytest.fixture
def security_guard():
    return PromptSecurityGuard()

def test_prompt_security_initialization(security_guard):
    assert security_guard is not None
    assert isinstance(security_guard, PromptSecurityGuard)
