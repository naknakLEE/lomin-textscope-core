from cryptography.fernet import Fernet

lomin_key = Fernet.generate_key()
kb_key = Fernet.generate_key()

with open("lomin.key", "wb") as f:
    f.write(lomin_key)
with open("kb.key", "wb") as f:
    f.write(kb_key)

with open("sample.txt", "rb") as f:
    sample = f.read()

lomin_fernet = Fernet(lomin_key)
kb_fernet = Fernet(kb_key)

encrypted_1 = lomin_fernet.encrypt(sample)
encrypted_2 = kb_fernet.encrypt(encrypted_1)

with open("text.txt.encrypted", "wb") as f:
    f.write(encrypted_2)

with open("text.txt.encrypted", "rb") as f:
    encrypted = f.read()

decrypted_1 = kb_fernet.decrypt(encrypted)
decrypted_2 = lomin_fernet.decrypt(decrypted_1)
print("Done")
