"""
Tests for authentication module
"""
import pytest
from app.core.auth import AuthManager, MFAManager


class TestAuthManager:
    """Test AuthManager class."""
    
    @pytest.fixture
    def auth_manager(self):
        return AuthManager()
    
    def test_create_token_pair(self, auth_manager: AuthManager):
        """Test token pair creation."""
        token_pair = auth_manager.create_token_pair(
            user_id="user-123",
            roles=["user"],
        )
        
        assert token_pair.access_token
        assert token_pair.refresh_token
        assert token_pair.expires_in > 0
        assert token_pair.refresh_expires_in > 0
    
    def test_verify_access_token(self, auth_manager: AuthManager):
        """Test access token verification."""
        token_pair = auth_manager.create_token_pair(
            user_id="user-456",
            roles=["user", "admin"],
        )
        
        payload = auth_manager.verify_token(token_pair.access_token, token_type="access")
        
        assert payload is not None
        assert payload.sub == "user-456"
        assert "user" in payload.roles
        assert "admin" in payload.roles
    
    def test_verify_refresh_token(self, auth_manager: AuthManager):
        """Test refresh token verification."""
        token_pair = auth_manager.create_token_pair(
            user_id="user-789",
            roles=["user"],
        )
        
        payload = auth_manager.verify_token(token_pair.refresh_token, token_type="refresh")
        
        assert payload is not None
        assert payload.sub == "user-789"
    
    def test_verify_invalid_token(self, auth_manager: AuthManager):
        """Test invalid token verification."""
        payload = auth_manager.verify_token("invalid-token", token_type="access")
        assert payload is None
    
    def test_refresh_access_token(self, auth_manager: AuthManager):
        """Test refreshing access token."""
        original = auth_manager.create_token_pair(
            user_id="user-refresh",
            roles=["user"],
        )
        
        new_pair = auth_manager.refresh_access_token(
            original.refresh_token,
            roles=["user"],
        )
        
        assert new_pair is not None
        assert new_pair.access_token != original.access_token


class TestMFAManager:
    """Test MFAManager class."""
    
    @pytest.fixture
    def mfa_manager(self):
        return MFAManager()
    
    def test_generate_secret(self, mfa_manager: MFAManager):
        """Test secret generation."""
        secret = mfa_manager.generate_secret()
        
        assert len(secret) == 32  # Base32 encoded
        assert secret.isalnum()
    
    def test_generate_unique_secrets(self, mfa_manager: MFAManager):
        """Test that secrets are unique."""
        secrets = [mfa_manager.generate_secret() for _ in range(10)]
        assert len(set(secrets)) == 10
    
    def test_get_provisioning_uri(self, mfa_manager: MFAManager):
        """Test provisioning URI generation."""
        secret = mfa_manager.generate_secret()
        email = "test@example.com"
        
        uri = mfa_manager.get_provisioning_uri(secret, email)
        
        assert uri.startswith("otpauth://totp/")
        assert "XOR" in uri
        # Email might be URL encoded
        assert email in uri or email.replace("@", "%40") in uri
    
    def test_generate_backup_codes(self, mfa_manager: MFAManager):
        """Test backup codes generation."""
        codes = mfa_manager.generate_backup_codes(count=8)
        
        assert len(codes) == 8
        assert len(set(codes)) == 8  # All unique
        
        for code in codes:
            assert len(code) == 8  # 8 character codes
    
    def test_encrypt_decrypt_secret(self, mfa_manager: MFAManager):
        """Test secret encryption/decryption."""
        secret = mfa_manager.generate_secret()
        user_id = "user-mfa-123"
        
        encrypted = mfa_manager.encrypt_secret(secret, user_id)
        decrypted = mfa_manager.decrypt_secret(encrypted, user_id)
        
        assert encrypted != secret
        assert decrypted == secret
