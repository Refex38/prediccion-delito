import pandas as pd
import numpy as np
import joblib
import folium
from datetime import datetime, timedelta, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import text

from core.database import engine
from core.config import MODEL_PATH, ENCODERS_PATH, COORDS_PATH, DF_ORIGINAL_PATH

# --- Variables Globales del Modelo ---
model = None
encoders = {}
colony_coords = {}
last_data_date = datetime(2024, 12, 31).date()

def cargar_recursos():
    """Carga los modelos entrenados y metadatos necesarios al inicio."""
    global model, encoders, colony_coords, last_data_date
    try:
        # Usamos las rutas absolutas seguras
        model = joblib.load(MODEL_PATH)
        encoders = joblib.load(ENCODERS_PATH)
        colony_coords = joblib.load(COORDS_PATH)
        print("Modelo cargado exitosamente.")
    except FileNotFoundError:
        print("Modelos no encontrados. Se requiere entrenamiento inicial.")

# Ejecutamos la carga al momento de importar este módulo
cargar_recursos()

def predecir_mapa_calor(fecha_obj, hora_int, municipio_str):
    """Genera un mapa de calor y una tabla de riesgos basados en la probabilidad de incidente."""
    if not model:
        return None, pd.DataFrame({"Estado": ["Modelo no disponible."]})
    
    if not fecha_obj:
        return None, pd.DataFrame({"Aviso": ["Por favor seleccione una fecha."]})
    
    # Normalización de fecha
    if isinstance(fecha_obj, str):
        fecha_seleccionada = pd.to_datetime(fecha_obj).date()
    else:
        fecha_seleccionada = pd.to_datetime(fecha_obj).date()
    
    if fecha_seleccionada > last_data_date:
        msg = f"Seleccione una fecha posterior al último registro histórico ({last_data_date.strftime('%d/%m/%Y')})."
        return None, pd.DataFrame({"Aviso": [msg]})

    try:
        dias_semana = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']
        dia_str = dias_semana[fecha_seleccionada.weekday()]
        
        colonias_list = list(colony_coords.keys())
        
        if not colonias_list:
            return None, pd.DataFrame({"Error": ["No hay información geográfica disponible."]})

        input_df = pd.DataFrame({
            'dia_hec': [dia_str] * len(colonias_list),
            'mpio': [municipio_str] * len(colonias_list),
            'colonia': colonias_list,
            'hora_hecho': [hora_int] * len(colonias_list)
        })
        
        for col in ['dia_hec', 'mpio', 'colonia']:
            le = encoders.get(col)
            if le:
                input_df[col] = input_df[col].apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
        
        valid_rows = input_df[(input_df['dia_hec'] != -1) & (input_df['mpio'] != -1) & (input_df['colonia'] != -1)]
        
        if valid_rows.empty:
            return None, pd.DataFrame({"Aviso": ["Municipio no reconocido en el modelo actual."]})

        probs = model.predict_proba(valid_rows)[:, 1]
        
        todos_resultados = []
        for idx, prob in zip(valid_rows.index, probs):
            col_name = colonias_list[idx]
            todos_resultados.append({
                "Colonia": col_name,
                "Probabilidad": prob,
                "Lat": colony_coords[col_name]['lat'],
                "Lon": colony_coords[col_name]['lon']
            })
            
        df_res = pd.DataFrame(todos_resultados)
        df_res = df_res[df_res['Probabilidad'] > 0.30]
        df_res = df_res.sort_values(by="Probabilidad", ascending=False).head(50)
        
        if df_res.empty:
             return None, pd.DataFrame({"Resultado": ["No se detectan zonas de alto riesgo para los parámetros seleccionados."]})

        mapa = folium.Map(location=[22.15, -100.98], zoom_start=12)
        resultados_tabla = []
        
        for _, row in df_res.iterrows():
            prob = row['Probabilidad']
            
            color = '#f1c40f'
            if prob > 0.4: color = '#2ecc71'
            if prob > 0.6: color = '#e67e22'
            if prob > 0.8: color = '#e74c3c'
            
            folium.Circle(
                location=[row['Lat'], row['Lon']],
                radius=150 + (prob * 300),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=f"<b>{row['Colonia']}</b><br>Riesgo estimado: {prob:.1%}",
                tooltip=f"{row['Colonia']}"
            ).add_to(mapa)
            
            resultados_tabla.append({
                "Colonia": row['Colonia'],
                "Riesgo": f"{prob:.1%}"
            })
        
        return mapa._repr_html_(), pd.DataFrame(resultados_tabla)

    except Exception:
        return None, pd.DataFrame({"Error": ["Ocurrió un error inesperado al generar la predicción."]})

def reentrenar_modelo_slp():
    """Re-entrena el modelo Random Forest con los últimos datos disponibles en la base de datos."""
    global model, encoders, colony_coords, last_data_date
    if not engine: return "Sin conexión a la base de datos."
    
    COOLDOWN_PERIOD = timedelta(hours=1)
    now_utc = datetime.now(timezone.utc)
    
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT last_trained_at FROM model_metadata WHERE model_name = 'slp_model'")).scalar()
            
            if res:
                if res.tzinfo is None:
                    res = res.replace(tzinfo=timezone.utc)
                
                time_diff = now_utc - res
                if time_diff < COOLDOWN_PERIOD:
                    remaining = COOLDOWN_PERIOD - time_diff
                    hours, remainder = divmod(remaining.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    return f"Re-entrenamiento en espera. Intente de nuevo en {hours}h {minutes}m."
            else:
                print("Procediendo con re-entrenamiento...")

            conn.execute(text("UPDATE model_metadata SET last_trained_at = :now WHERE model_name = 'slp_model'"), {"now": now_utc})
            conn.commit()
        
        df = pd.read_sql("SELECT * FROM ROBO_CASA_HABITACION_MODELO", con=engine)
        if df.empty: return "No hay suficientes datos para entrenar."
        
        df.columns = [str(c) for c in df.columns]
        df = df.rename(columns={'municipio': 'mpio', 'dia_hechos': 'dia_hec', 'hora_hechos': 'hora_hecho'})

        if pd.api.types.is_timedelta64_dtype(df['hora_hecho']):
             df['hora_hecho'] = df['hora_hecho'].dt.components['hours']
        else:
            df['hora_hecho'] = pd.to_numeric(df['hora_hecho'].astype(str).str.split(':').str[0], errors='coerce').fillna(0).astype(int)

        features = ['dia_hec', 'mpio', 'colonia', 'hora_hecho']
        
        pos_df = df[features].copy(); pos_df['target'] = 1
        neg_df = pos_df.copy()
        neg_df['colonia'] = np.random.permutation(neg_df['colonia'].values)
        neg_df['hora_hecho'] = np.random.randint(0, 24, size=len(neg_df))
        neg_df['target'] = 0
        
        train_df = pd.concat([pos_df, neg_df], ignore_index=True)
        
        new_encs = {}
        X = train_df[features].copy()
        for c in ['dia_hec', 'mpio', 'colonia']:
            le = LabelEncoder()
            X[c] = X[c].astype(str)
            le.fit(X[c])
            X[c] = le.transform(X[c])
            new_encs[c] = le
            
        clf = RandomForestClassifier(n_estimators=100, n_jobs=-1)
        X.columns = [str(c) for c in X.columns]
        clf.fit(X, train_df['target'])
        
        df['x_casa'] = pd.to_numeric(df['x_casa'], errors='coerce')
        df['y_casa'] = pd.to_numeric(df['y_casa'], errors='coerce')

        cds = df.groupby('colonia')[['x_casa', 'y_casa']].mean().to_dict(orient='index')
        new_coords = {k: {'lat': v['x_casa'], 'lon': v['y_casa']} for k,v in cds.items()}
        
        joblib.dump(clf, MODEL_PATH)
        joblib.dump(new_encs, ENCODERS_PATH)
        joblib.dump(new_coords, COORDS_PATH)
        joblib.dump(df, DF_ORIGINAL_PATH) 
        
        model = clf
        encoders = new_encs
        colony_coords = new_coords
        
        return "Modelo actualizado exitosamente."

    except Exception as e:
        with engine.connect() as conn:
            reset_time = now_utc - timedelta(days=1)
            conn.execute(text("UPDATE model_metadata SET last_trained_at = :reset WHERE model_name = 'slp_model'"), {"reset": reset_time})
            conn.commit()   
        return f"Error durante el entrenamiento. Intente nuevamente."