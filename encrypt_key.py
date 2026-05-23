from cryptography.fernet import Fernet

# Keep this key in sync with main.py and firebase_sync.py.
FIREBASE_SECRET_KEY = b'J6TmP2PtNyXGZX28P8b2_CO2xRJ2c-xk2AIIJtu1gPc='

print("Using Firebase key:", FIREBASE_SECRET_KEY.decode())

cipher = Fernet(FIREBASE_SECRET_KEY)

with open("serviceAccountKey.json", "rb") as f:
    encrypted = cipher.encrypt(f.read())

with open("serviceAccountKey.enc", "wb") as f:
    f.write(encrypted)

print("Encrypted file created: serviceAccountKey.enc")
