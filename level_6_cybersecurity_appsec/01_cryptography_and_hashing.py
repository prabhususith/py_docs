r"""
Enterprise Cryptography: OWASP Password Hashing & Fernet Symmetric Encryption
=============================================================================
Description: Production application security module covering cryptographic password hashing
             using PBKDF2-HMAC-SHA256 (600,000 iterations per OWASP recommendations),
             constant-time verification to prevent side-channel timing attacks, and symmetric
             authenticated encryption (Fernet: AES-128-CBC + HMAC-SHA256) for PII data protection.
Enterprise Mapping:
- Password Hashing (PBKDF2): Counterpart to Node.js `crypto.pbkdf2` and PHP `password_hash()`
  (`PASSWORD_ARGON2ID` / `PASSWORD_BCRYPT`). Employs cryptographically secure random salts and
  work-factor iterations to resist GPU-accelerated brute-force attacks.
- Constant-Time Comparison (`hmac.compare_digest`): Eliminates timing side-channels present in standard
  equality operators (`==`). Directly corresponds to `crypto.timingSafeEqual` in Node.js and
  `hash_equals()` in PHP.
- Fernet Symmetric Encryption: Standard cryptographic envelope guaranteeing both confidentiality
  and authenticity (ciphertext tampering causes decryption to fail immediately). Replaces manual
  OpenSSL AES cipher orchestration in PHP and Node.js.

Official Documentation References:
- Cryptography Fernet Documentation: https://cryptography.io/en/latest/fernet/
- Python Hashlib Module: https://docs.python.org/3/library/hashlib.html
- Python Secrets Module: https://docs.python.org/3/library/secrets.html
- OWASP Password Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from typing import Final, NamedTuple

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# ==============================================================================
# 1. OWASP-Compliant Password Hashing & Constant-Time Verification
# ==============================================================================
class PasswordHashRecord(NamedTuple):
    algorithm: str
    iterations: int
    salt_hex: str
    hash_hex: str

    def serialize(self) -> str:
        """Format as standard crypt-style record: algorithm$iterations$salt$hash."""
        return f"{self.algorithm}${self.iterations}${self.salt_hex}${self.hash_hex}"

    @classmethod
    def deserialize(cls, encoded_str: str) -> PasswordHashRecord:
        """Parse serialized password record."""
        parts = encoded_str.split("$")
        if len(parts) != 4:
            raise ValueError("Malformed password hash format.")
        return cls(
            algorithm=parts[0],
            iterations=int(parts[1]),
            salt_hex=parts[2],
            hash_hex=parts[3],
        )


class EnterprisePasswordHasher:
    """
    Implements OWASP 2024+ password storage standards.
    Uses PBKDF2-HMAC-SHA256 with 600,000 iterations and 128-bit cryptographically secure salts.
    """

    ALGORITHM: Final[str] = "pbkdf2_sha256"
    ITERATIONS: Final[int] = 600_000
    SALT_BYTES: Final[int] = 16
    KEY_LENGTH: Final[int] = 32

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        """Generate cryptographically salted hash using CSPRNG salt."""
        salt: bytes = secrets.token_bytes(cls.SALT_BYTES)
        derived_key: bytes = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=plain_password.encode("utf-8"),
            salt=salt,
            iterations=cls.ITERATIONS,
            dklen=cls.KEY_LENGTH,
        )
        record = PasswordHashRecord(
            algorithm=cls.ALGORITHM,
            iterations=cls.ITERATIONS,
            salt_hex=salt.hex(),
            hash_hex=derived_key.hex(),
        )
        return record.serialize()

    @classmethod
    def verify_password(cls, plain_password: str, serialized_hash: str) -> bool:
        """
        Verify password against stored hash record.
        Uses `hmac.compare_digest` to ensure constant-time execution,
        immunizing the application against remote timing side-channel attacks.
        """
        try:
            record = PasswordHashRecord.deserialize(serialized_hash)
        except Exception:
            # Constant-time dummy computation prevents username enumeration timing leaks
            hashlib.pbkdf2_hmac("sha256", b"dummy", b"dummy_salt_1234", cls.ITERATIONS, cls.KEY_LENGTH)
            return False

        salt: bytes = bytes.fromhex(record.salt_hex)
        expected_key: bytes = bytes.fromhex(record.hash_hex)

        actual_key: bytes = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=plain_password.encode("utf-8"),
            salt=salt,
            iterations=record.iterations,
            dklen=len(expected_key),
        )

        # Constant-time comparison: O(1) irrespective of mismatch position
        return hmac.compare_digest(actual_key, expected_key)


# ==============================================================================
# 2. Symmetric Authenticated Encryption (Fernet: AES-128-CBC + HMAC)
# ==============================================================================
class PIIEncryptionService:
    """
    Encrypts sensitive Personally Identifiable Information (PII) at rest.
    Uses Fernet:
      - AES-128-CBC encryption with PKCS7 padding
      - HMAC-SHA256 authentication tag
      - 128-bit initialization vector (IV) generated per message
    """

    def __init__(self, master_key_base64: str | None = None) -> None:
        if master_key_base64 is None:
            # Generate new 32-byte URL-safe base64 key
            self.key: bytes = Fernet.generate_key()
        else:
            self.key = master_key_base64.encode("utf-8")
        self.cipher: Fernet = Fernet(self.key)

    @classmethod
    def derive_key_from_passphrase(cls, passphrase: str, salt: bytes) -> str:
        """Derive a URL-safe base64 Fernet key from a high-entropy passphrase."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480_000,
        )
        derived = kdf.derive(passphrase.encode("utf-8"))
        return base64.urlsafe_b64encode(derived).decode("utf-8")

    def encrypt_pii(self, plaintext: str) -> str:
        """Encrypt plaintext string into authenticated base64 ciphertext token."""
        ciphertext_bytes: bytes = self.cipher.encrypt(plaintext.encode("utf-8"))
        return ciphertext_bytes.decode("utf-8")

    def decrypt_pii(self, ciphertext: str) -> str:
        """
        Decrypt and verify authenticity of ciphertext.
        Raises InvalidToken if data was modified, corrupted, or re-keyed.
        """
        try:
            plaintext_bytes: bytes = self.cipher.decrypt(ciphertext.encode("utf-8"))
            return plaintext_bytes.decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Ciphertext authentication failed: data tampering or wrong encryption key.") from exc


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
def main() -> None:
    print("=" * 70)
    print(" LEVEL 6: 01_CRYPTOGRAPHY_AND_HASHING - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Password Hashing & Timing-Attack Proof Verification
    print("\n--- 1. OWASP PBKDF2-HMAC-SHA256 Password Hashing ---")
    secret_pass = "EnterpriseP@ssw0rd!2026#Secure"

    print(f"  Hashing plain password using {EnterprisePasswordHasher.ITERATIONS:,} iterations...")
    hashed_record = EnterprisePasswordHasher.hash_password(secret_pass)
    print(f"  Generated Hash Record:\n    {hashed_record[:65]}...")

    # Positive Verification
    is_valid = EnterprisePasswordHasher.verify_password(secret_pass, hashed_record)
    print(f"  Password Verification with correct secret: {is_valid}")
    assert is_valid is True

    # Negative Verification
    is_invalid = EnterprisePasswordHasher.verify_password("WrongPassword123", hashed_record)
    print(f"  Password Verification with incorrect secret: {is_invalid}")
    assert is_invalid is False
    print("  [PASS] PBKDF2 hashing and constant-time compare_digest validated.")

    # 2. PII Symmetric Authenticated Encryption (Fernet)
    print("\n--- 2. Fernet Symmetric PII Encryption & Authenticity Guard ---")
    pii_service = PIIEncryptionService()

    sensitive_payload = "SSN: 987-65-4321 | Card: 4111-2222-3333-4444 | DOB: 1985-04-12"
    print(f"  Original PII Plaintext: '{sensitive_payload}'")

    encrypted_token = pii_service.encrypt_pii(sensitive_payload)
    print(f"  Encrypted Ciphertext Token:\n    {encrypted_token}")

    decrypted_payload = pii_service.decrypt_pii(encrypted_token)
    print(f"  Decrypted Plaintext:    '{decrypted_payload}'")
    assert decrypted_payload == sensitive_payload
    print("  [PASS] Encryption and decryption cycle completed with 100% fidelity.")

    # 3. Tampering & Authenticity Defense
    print("\n--- 3. Ciphertext Tampering Attack Defense ---")
    # Mutate 1 byte in the base64 ciphertext
    token_chars = list(encrypted_token)
    token_chars[20] = "X" if token_chars[20] != "X" else "Y"
    tampered_token = "".join(token_chars)

    try:
        pii_service.decrypt_pii(tampered_token)
        raise AssertionError("Decryption succeeded on tampered ciphertext! HMAC authentication failed.")
    except ValueError as err:
        print(f"  [SECURITY VERIFIED] HMAC signature detected ciphertext tampering: {err}")

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 01_cryptography_and_hashing module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    main()
