import frappe
from cryptography.fernet import Fernet

def get_encryption_key():
    """
    Retrieve encryption key from site config.
    """
    key = frappe.conf.get("encryption_key")
    if not key:
        frappe.throw("Encryption key not found in site config. Cannot perform encryption operations.")
    return key

def encrypt_data(data):
    """
    Encrypt sensitive data string.
    """
    if not data:
        return data
    
    key = get_encryption_key()
    f = Fernet(key)
    if isinstance(data, str):
        data = data.encode("utf-8")
    
    encrypted = f.encrypt(data)
    return encrypted.decode("utf-8")

def decrypt_data(encrypted_data):
    """
    Decrypt sensitive data string.
    """
    if not encrypted_data:
        return encrypted_data
        
    key = get_encryption_key()
    f = Fernet(key)
    
    if isinstance(encrypted_data, str):
        encrypted_data = encrypted_data.encode("utf-8")
        
    decrypted = f.decrypt(encrypted_data)
    return decrypted.decode("utf-8")
