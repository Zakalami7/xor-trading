"""
Run tests with proper environment configuration
"""
import os
import sys

# Set environment variables BEFORE importing anything
os.environ["ENVIRONMENT"] = "development"
os.environ["SECRET_KEY"] = "test-secret-key-for-dev-only123"
os.environ["JWT_SECRET_KEY"] = "jwt-secret-key-for-testing1234"
os.environ["ENCRYPTION_KEY"] = "12345678901234567890123456789012"  # 32 bytes
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["DEBUG"] = "true"

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["-v", "--tb=short", "tests/"]))
