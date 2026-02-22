from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / 'slp_model.joblib'
ENCODERS_PATH = BASE_DIR / 'slp_encoders.joblib'
COORDS_PATH = BASE_DIR / 'slp_coords.joblib'
DF_ORIGINAL_PATH = BASE_DIR / 'df_original_para_app.joblib'

LOGO_PATH = BASE_DIR / 'logo_upslp.jpg'
