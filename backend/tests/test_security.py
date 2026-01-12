"""
Tests for security module
"""
import pytest
from app.core.security import SecurityManager


class TestSecurityManager:
    """Test SecurityManager class."""
    
    def test_hash_password(self, security_manager: SecurityManager):
        """Test password hashing."""
        password = "SecurePassword123"
        hashed = security_manager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert security_manager.verify_password(password, hashed)
    
    def test_verify_password_wrong(self, security_manager: SecurityManager):
        """Test password verification with wrong password."""
        password = "SecurePassword123"
        wrong_password = "WrongPassword123"
        hashed = security_manager.hash_password(password)
        
        assert not security_manager.verify_password(wrong_password, hashed)
    
    def test_encrypt_decrypt_api_key(self, security_manager: SecurityManager):
        """Test API key encryption and decryption."""
        api_key = "my-super-secret-api-key"
        user_id = "user-123"
        
        encrypted = security_manager.encrypt_api_key(api_key, user_id)
        decrypted = security_manager.decrypt_api_key(encrypted, user_id)
        
        assert encrypted != api_key
        assert decrypted == api_key
    
    def test_encrypt_different_users(self, security_manager: SecurityManager):
        """Test that same key encrypts differently for different users."""
        api_key = "my-api-key"
        
        encrypted_1 = security_manager.encrypt_api_key(api_key, "user-1")
        encrypted_2 = security_manager.encrypt_api_key(api_key, "user-2")
        
        # Different ciphertexts due to different AAD and nonce
        assert encrypted_1 != encrypted_2
    
    def test_generate_hmac(self, security_manager: SecurityManager):
        """Test HMAC generation."""
        data = "some-data-to-sign"
        
        hmac1 = security_manager.generate_hmac(data)
        hmac2 = security_manager.generate_hmac(data)
        
        # Same data should produce same HMAC
        assert hmac1 == hmac2
        assert len(hmac1) > 0
    
    def test_generate_hmac_different_data(self, security_manager: SecurityManager):
        """Test HMAC with different data."""
        hmac1 = security_manager.generate_hmac("data-1")
        hmac2 = security_manager.generate_hmac("data-2")
        
        assert hmac1 != hmac2
