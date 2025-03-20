import bcrypt
import os
from uuid import uuid4
import hmac
import hashlib
from app.db.models.models import Usuario
from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
EXPIRATION_HOURS = int(os.getenv("EXPIRATION_HOURS"))


def generar_token_activacion():
    token = uuid4().hex
    signature = hmac.new(SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
    return f"{token}.{signature}" 


def verificar_token(token: str, usuario: Usuario):
    if not usuario:
        raise ValueError("Usuario no existe")
    
    if not usuario.email_verification_token:
        raise ValueError("Token no configurado")
    
    if datetime.now() > usuario.email_verification_expiration:
        raise ValueError("Token expirado")
    
    if not bcrypt.checkpw(token.encode(), usuario.email_verification_token.encode()):
        raise ValueError("Token inválido")    


def crear_token(email: str):
    token = uuid4().hex + email
    hashed_token = bcrypt.hashpw(token.encode(), bcrypt.gensalt())    
    expiracion = datetime.now() + timedelta(hours=1)    
    expiracion_str = expiracion.isoformat()
    
    return token, hashed_token.decode(), expiracion_str