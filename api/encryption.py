# api/encryption.py

import base64
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import json
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """
    Handles end-to-end encryption for messages using RSA for key exchange
    and AES for message content encryption.
    """
    
    @staticmethod
    def generate_rsa_key_pair():
        """Generate a new RSA key pair for a user."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return {
            'private_key': private_pem.decode('utf-8'),
            'public_key': public_pem.decode('utf-8')
        }
    
    @staticmethod
    def generate_aes_key():
        """Generate a random AES key for symmetric encryption."""
        return os.urandom(32)  # 256-bit key
    
    @staticmethod
    def encrypt_with_aes(plaintext: str, key: bytes) -> dict:
        """Encrypt text with AES-GCM."""
        try:
            # Generate random IV
            iv = os.urandom(12)  # 96-bit IV for GCM
            
            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            
            # Encrypt the plaintext
            ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()
            
            # Return encrypted data with IV and authentication tag
            return {
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'iv': base64.b64encode(iv).decode('utf-8'),
                'tag': base64.b64encode(encryptor.tag).decode('utf-8')
            }
        except Exception as e:
            logger.error(f"AES encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt_with_aes(encrypted_data: dict, key: bytes) -> str:
        """Decrypt text with AES-GCM."""
        try:
            # Decode base64 data
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            iv = base64.b64decode(encrypted_data['iv'])
            tag = base64.b64decode(encrypted_data['tag'])
            
            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            
            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"AES decryption failed: {e}")
            raise
    
    @staticmethod
    def encrypt_with_rsa(data: bytes, public_key_pem: str) -> str:
        """Encrypt data with RSA public key."""
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            encrypted = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"RSA encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt_with_rsa(encrypted_data: str, private_key_pem: str) -> bytes:
        """Decrypt data with RSA private key."""
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            decrypted = private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted
        except Exception as e:
            logger.error(f"RSA decryption failed: {e}")
            raise

class MessageEncryption:
    """
    Handles message encryption for different conversation types.
    """
    
    @staticmethod
    def encrypt_private_message(content: str, sender_public_key: str, receiver_public_key: str) -> dict:
        """
        Encrypt message for private conversation using hybrid encryption.
        Generate AES key, encrypt message with AES, encrypt AES key with both users' RSA keys.
        """
        try:
            # Generate AES key for this message
            aes_key = EncryptionManager.generate_aes_key()
            
            # Encrypt message content with AES
            encrypted_content = EncryptionManager.encrypt_with_aes(content, aes_key)
            
            # Encrypt AES key for both sender and receiver
            encrypted_keys = {
                'sender_encrypted_key': EncryptionManager.encrypt_with_rsa(aes_key, sender_public_key),
                'receiver_encrypted_key': EncryptionManager.encrypt_with_rsa(aes_key, receiver_public_key)
            }
            
            # Combine everything
            return {
                'encrypted_content': json.dumps(encrypted_content),
                'encrypted_keys': json.dumps(encrypted_keys)
            }
        except Exception as e:
            logger.error(f"Private message encryption failed: {e}")
            raise
    
    @staticmethod
    def encrypt_group_message(content: str, conversation_key: bytes) -> dict:
        """
        Encrypt message for group/community conversation using shared key.
        """
        try:
            encrypted_content = EncryptionManager.encrypt_with_aes(content, conversation_key)
            return {
                'encrypted_content': json.dumps(encrypted_content),
                'encrypted_keys': ''  # No individual keys needed for group messages
            }
        except Exception as e:
            logger.error(f"Group message encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt_message(encrypted_content: str, encrypted_keys: str, user_private_key: str = None, conversation_key: bytes = None) -> str:
        """
        Decrypt message based on available keys.
        """
        try:
            content_data = json.loads(encrypted_content)
            
            if conversation_key:
                # Group/community message - use shared key
                return EncryptionManager.decrypt_with_aes(content_data, conversation_key)
            elif user_private_key and encrypted_keys:
                # Private message - decrypt AES key first
                keys_data = json.loads(encrypted_keys)
                
                # Try to decrypt with either sender or receiver key
                aes_key = None
                for key_type in ['sender_encrypted_key', 'receiver_encrypted_key']:
                    if key_type in keys_data:
                        try:
                            aes_key = EncryptionManager.decrypt_with_rsa(keys_data[key_type], user_private_key)
                            break
                        except:
                            continue
                
                if aes_key:
                    return EncryptionManager.decrypt_with_aes(content_data, aes_key)
                else:
                    raise Exception("Unable to decrypt AES key")
            else:
                raise Exception("Insufficient decryption parameters")
                
        except Exception as e:
            logger.error(f"Message decryption failed: {e}")
            raise
