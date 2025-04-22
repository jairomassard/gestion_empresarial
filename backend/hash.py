import bcrypt

password = "superadmin123"  # Cambia esto por la contraseña deseada
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hashed)