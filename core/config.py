# core/config.py
from pathlib import Path

# __file__ es la ruta de este archivo (core/config.py)
# .resolve() obtiene la ruta absoluta completa
# .parent.parent sube dos niveles para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Definimos las rutas exactas a los recursos que necesitamos
MODEL_PATH = BASE_DIR / 'slp_model.joblib'
ENCODERS_PATH = BASE_DIR / 'slp_encoders.joblib'
COORDS_PATH = BASE_DIR / 'slp_coords.joblib'
DF_ORIGINAL_PATH = BASE_DIR / 'df_original_para_app.joblib'

LOGO_PATH = BASE_DIR / 'logo_upslp.jpg'