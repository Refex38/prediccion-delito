import os
import tempfile
import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from core.database import engine
from core.config import LOGO_PATH

def generar_reporte_slp(formato):
    """Consulta los últimos registros y genera un archivo PDF o Excel."""
    if not engine: return None
    
    try:
        limit_rows = 1000
        df = pd.read_sql(f"SELECT * FROM ROBO_CASA_HABITACION_MODELO ORDER BY fecha_hechos DESC LIMIT {limit_rows}", con=engine)
        if df.empty: return None
        
        cols_drop = ['id_robo_casa', 'created_at']
        df = df.drop(columns=[c for c in cols_drop if c in df.columns])
        
        if 'hora_hechos' in df.columns:
            df['hora_hechos'] = df['hora_hechos'].astype(str).str.replace('0 days ', '')
        
        temp_dir = tempfile.gettempdir() 
        unique_name = f"reporte_delitos_slp.{formato}"
        filename = os.path.join(temp_dir, unique_name)
        
        print(f"Generando archivo en: {filename}", flush=True)
        
        if formato == "xlsx":
            # Limpieza de zonas horarias para Excel
            for col in df.select_dtypes(include=['datetime', 'datetimetz']).columns:
                if df[col].dt.tz is not None: df[col] = df[col].dt.tz_localize(None)

            df.to_excel(filename, index=False)

        else:
            pdf = FPDF(orientation='L', format='A4')
            pdf.add_page()

            if LOGO_PATH.exists(): 
                pdf.image(str(LOGO_PATH), x=10, y=8, w=25)
            
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 10, "Reporte de Delitos de Robo a Casa Habitación SLP", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            
            pdf.set_font("Helvetica", 'I', 10)
            pdf.cell(0, 8, f"Nota: Muestra los últimos {limit_rows} registros procesados.", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            pdf.ln(5)
            
            cols = ['fecha_hechos', 'hora_hechos', 'municipio', 'colonia', 'motivo']
            col_width = pdf.w / (len(cols) + 1)
            
            pdf.set_font("Helvetica", 'B', 8)
            for c in cols: pdf.cell(col_width, 10, c, border=1)
            pdf.ln()
            
            pdf.set_font("Helvetica", '', 8)
            for _, row in df.head(limit_rows).iterrows():
                for c in cols:
                    valor = str(row.get(c, ''))[:25]
                    pdf.cell(col_width, 10, valor, border=1)
                pdf.ln()
            
            pdf.output(filename)
            
        return filename

    except Exception as e:
        print(f"Error generando el reporte: {e}")
        return None