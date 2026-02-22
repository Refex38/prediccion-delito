import os
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()

def get_db_engine():
    """
    Construye y verifica la conexión a la base de datos MySQL.
    """
    DB_HOST = os.environ.get("DB_HOST")
    DB_USER = os.environ.get("DB_USER")
    DB_PASS = os.environ.get("DB_PASS")
    DB_NAME = os.environ.get("DB_NAME")
    DB_PORT = os.environ.get("DB_PORT")
    
    # Verificación temprana: Aseguramos que todas las variables existan
    if not all([DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT]):
        print("Advertencia: Faltan credenciales en el archivo .env. Funcionalidades de DB limitadas.")
        return None

    DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    try:
        # pool_pre_ping=True verifica que la conexión esté viva antes de cada consulta
        engine = sqlalchemy.create_engine(DB_URL, pool_pre_ping=True)
        
        with engine.connect() as conn:
            pass 
            
        print("Conexión a la base de datos exitosa.")
        return engine
        
    except Exception as e:
        print(f"Advertencia: Sin conexión. Funcionalidades limitadas. Detalle del error: {e}")
        return None

engine = get_db_engine()
