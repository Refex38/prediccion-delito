import pandas as pd
from core.database import engine

def subir_csv_slp(file_obj):
    """Procesa la carga masiva de archivos CSV hacia la base de datos."""
    if not engine: return "Error: Sin conexión a base de datos."
    if not file_obj: return "Error: No se seleccionó ningún archivo."
    
    try:
        try: 
            df = pd.read_csv(file_obj.name, dtype=str, encoding='utf-8-sig')
        except: 
            df = pd.read_csv(file_obj.name, dtype=str, encoding='latin1')
        
        df.columns = df.columns.str.strip().str.lower()
        df.columns = df.columns.str.replace('ï»¿', '', regex=False)
        df.columns = df.columns.str.replace(r'^[^a-z0-9]+', '', regex=True)

        mapping = {
            'fecha': 'fecha_registro', 'fecha_registro': 'fecha_registro',
            'hora_hec': 'hora_hechos', 'hora_hechos': 'hora_hechos',
            'fecha_hec': 'fecha_hechos', 'fecha_hechos': 'fecha_hechos',
            'dia_hec': 'dia_hechos', 'dia_hechos': 'dia_hechos',
            'region': 'region', 'region': 'region',
            'mpio': 'municipio', 'municipio': 'municipio',
            'calle': 'calle', 
            'numero': 'numero',
            'xcasa': 'x_casa', 'x_casa': 'x_casa',
            'ycasa': 'y_casa', 'y_casa': 'y_casa',
            'entrecalle': 'entre_calle',
            'ycalle': 'y_calle', 
            'estado': 'estado', 
            'colonia': 'colonia',
            'motivo': 'motivo'
        }
        df = df.rename(columns=mapping)
        
        if 'fecha_registro' in df.columns:
            df['fecha_registro'] = pd.to_datetime(df['fecha_registro'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
        if 'fecha_hecho' in df.columns:
            df['fecha_hecho'] = pd.to_datetime(df['fecha_hecho'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
            
        df = df.dropna(subset=['fecha_registro'])
        
        valid_cols = list(set(mapping.values()))
        df = df[df.columns.intersection(valid_cols)].copy()
        
        # Inserción a la base de datos usando el engine centralizado
        df.to_sql('ROBO_CASA_HABITACION_MODELO', con=engine, if_exists='append', index=False)
        return f"Carga exitosa: {len(df)} registros recibidos."
    except Exception as e: 
        return f"Error: El archivo no tiene el formato esperado. Detalle: {e}"


def guardar_manual_slp(
    fecha, hora, municipio, colonia, calle, ycalle, estado, numero, 
    entre_calle, region, latitud, longitud, motivo
):
    """Guarda un registro manual de un incidente en la base de datos."""
    if not engine: 
        return "Error: Sin conexión.", "", "", municipio, "", "", "", "", "", "", "", "", "", ""
    
    if not all([fecha, hora, municipio, colonia, motivo]):
        return "Error: Fecha, Hora, Municipio, Colonia y Motivo son obligatorios.", "", "", municipio, "", "", "", "", "", "", "", "", "", ""

    try:
        fecha_dt = pd.to_datetime(fecha)
        dias_es = {
            0: 'LUNES', 1: 'MARTES', 2: 'MIERCOLES', 3: 'JUEVES', 
            4: 'VIERNES', 5: 'SABADO', 6: 'DOMINGO'
        }
        dia_semana = dias_es[fecha_dt.weekday()]
    except:
        return "Error: Formato de fecha inválido (Use YYYY-MM-DD).", "", "", municipio, "", "", "", "", "", "", "", "", "", ""

    try:
        if latitud and longitud:
            float(latitud)
            float(longitud)
    except:
        return "Error: Latitud y Longitud deben ser números.", "", "", municipio, "", "", "", "", "", "", "", "", "", ""

    try:
        nuevo_dato = pd.DataFrame([{
            'fecha_registro': fecha if fecha else '', 
            'hora_hechos': hora if hora else '',
            'fecha_hechos': fecha if fecha else '',
            'dia_hechos': dia_semana if dia_semana else '',
            'region': region.upper() if region else '',
            'municipio': municipio.upper(),
            'calle': calle.upper() if calle else '',
            'numero': str(numero) if numero else '',
            'x_casa': str(latitud) if latitud else '',
            'y_casa': str(longitud) if longitud else '',
            'entre_calle': entre_calle.upper() if entre_calle else '',
            'y_calle': ycalle.upper() if ycalle else '',
            'estado': estado.upper() if estado else '',
            'colonia': colonia.upper() if colonia else '',
            'motivo': motivo.upper() if motivo else ''
        }])
        
        nuevo_dato.to_sql('ROBO_CASA_HABITACION_MODELO', con=engine, if_exists='append', index=False)
        return "Registro guardado.", "", "", municipio, "", "", "", "", "", "", "", "", "", ""
        
    except Exception:
        return "Error al guardar los datos", "", "", municipio, "", "", "", "", "", "", "", "", "", ""