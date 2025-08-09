import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Classe de configuração base para a aplicação.
    """
    SECRET_KEY = os.getenv('SECRET_KEY') or 'uma-chave-secreta-bem-dificil'
    
    MONGO_URI = os.getenv('MONGO_URI')