# Contract Tests

Consumer-Driven Contract Tests (CDCT) to prevent semantic drift.

## Purpose

Contract tests ensure that:
1. Providers implement behavior that consumers actually need
2. Consumers and providers agree on semantics (not just signatures)
3. Semantic drift is caught before integration

## Structure

```
tests/contracts/
+-- README.md
+-- test_{interface}_contract.py  # Contract tests per interface
+-- conftest.py                    # Shared fixtures
```

## Writing Contract Tests

**Consumers write these tests** to specify what they need from providers.

```python
# test_user_repository_contract.py
# Written by: API unit (consumer)
# Tests: UserRepository (provider)

class TestUserRepositoryContract:
    """Contract: What API unit requires from UserRepository"""
    
    def test_find_by_id_returns_none_for_missing(self, repo):
        """CRITICAL: We expect None, not an exception"""
        result = repo.find_by_id(UserId("nonexistent"))
        assert result is None
    
    def test_save_is_idempotent(self, repo):
        """CRITICAL: Saving twice should not create duplicates"""
        user = User(UserId("123"), Email("test@test.com"))
        repo.save(user)
        repo.save(user)
        # Should still be findable as single user
        assert repo.find_by_id(UserId("123")) == user
```

## Rules

1. **Consumers write contract tests** for interfaces they depend on
2. **Providers must pass** all consumer contract tests
3. **Breaking changes require discussion** before modifying contracts
4. **Document critical semantics** in test docstrings
