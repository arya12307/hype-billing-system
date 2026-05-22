from cryptography.fernet import Fernet

# Generate key (SAVE THIS KEY SAFELY)
key = Fernet.generate_key()
print("SAVE THIS KEY:", key.decode())

cipher = Fernet(key)

with open("serviceAccountKey.json", "rb") as f:
    encrypted = cipher.encrypt(f.read())

with open("serviceAccountKey.enc", "wb") as f:
    f.write(encrypted)

print("Encrypted file created: serviceAccountKey.enc")
