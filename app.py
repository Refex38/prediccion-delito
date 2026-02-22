# app.py
import gradio as gr

# Importamos las funciones y variables necesarias de nuestros servicios
from services.ml_service import predecir_mapa_calor, reentrenar_modelo_slp, encoders
from services.data_service import subir_csv_slp, guardar_manual_slp
from services.report_service import generar_reporte_slp

# --- INTERFAZ GRÁFICA ---

with gr.Blocks(title="Predicción del delito SLP") as demo:
    
    gr.Markdown("# Predicción del Delito Robo a Casa Habitación - San Luis Potosí")
    
    with gr.Tabs():
        
        # --- TAB 1: PREDICCIÓN ---
        with gr.Tab("Predicción"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Modelo de Predicción")
                    gr.Markdown("""
                    > **ℹ️ Información del Modelo**
                    > * **Nota:** La precisión disminuye cuanto mas lejano es el parametro de fecha.
                    """)
                    
                    in_fecha = gr.DateTime(label="Fecha de Predicción", include_time=False)
                    in_hora = gr.Slider(0, 23, step=1, label="Hora del día", value=20)
                    
                    mpios_opts = ["SAN LUIS POTOSI"]
                    in_mpio = gr.Textbox(label="Municipio", value="SAN LUIS POTOSI", interactive=False)
                    
                    btn_mapa = gr.Button("Predecir Zonas", variant="primary")
                
                with gr.Column(scale=2):
                    gr.Markdown("### Zonas Críticas")
                    out_tabla = gr.DataFrame(label="", headers=["Colonia", "Riesgo"])
                
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Mapa de Calor")
                    out_mapa = gr.HTML(label="Mapa de Calor")

            btn_mapa.click(predecir_mapa_calor, inputs=[in_fecha, in_hora, in_mpio], outputs=[out_mapa, out_tabla])

        # --- TAB 2: GESTIÓN ---
        with gr.Tab("Cargar Datos"):
            gr.Markdown("### Cargar Datos a traves de CSV")
            gr.Markdown("## El formato del CSV debe ser el siguiente: ")
            gr.Markdown("fecha, hora_hec, fecha_hec, dia_hec, region, mpio, colonia, calle, numero, xcasa, ycasa, entrecalle, ycalle, estado, motivo.")
            with gr.Row():
                in_csv = gr.File(label="CSV (Formato SLP)", file_types=[".csv"])
            with gr.Row():
                btn_csv = gr.Button("Subir CSV")
            
            gr.Markdown("---")
            gr.Markdown("### Registro Manual Completo")
            
            # Protección en caso de que los encoders no se hayan generado aún
            list_colonias = sorted(list(encoders['colonia'].classes_)) if encoders and 'colonia' in encoders else []
            list_motivos = ["ROBO A CASA HABITACION"]

            with gr.Row():
                man_fecha = gr.Textbox(placeholder="YYYY-MM-DD", label="Fecha del Hecho*")
                man_hora = gr.Textbox(placeholder="HH:MM", label="Hora (24h)*")
            
            with gr.Row():
                man_region = gr.Textbox(label="Región (Ej: CENTRO)")
                man_mpio = gr.Textbox(label="Municipio", value="SAN LUIS POTOSI", interactive=False)
                man_col = gr.Textbox(label="Colonia*")
            
            with gr.Row():
                man_calle = gr.Textbox(label="Calle Principal")
                man_numero = gr.Textbox(label="Número Ext.")
                man_entre = gr.Textbox(label="Entre Calle")
                man_ycalle = gr.Textbox(label="Y Calle")

            with gr.Row():
                man_estado = gr.Textbox(label="Estado", value="SAN LUIS POTOSI", interactive=False)
                man_lat = gr.Textbox(label="Latitud (Ej: 22.15)*")
                man_lon = gr.Textbox(label="Longitud (Ej: -100.98)*")
                man_motivo = gr.Textbox(label="Motivo")

            btn_manual = gr.Button("Guardar Registro", variant="primary")

            with gr.Row():
                out_status = gr.Textbox(label="Estatus del Sistema", interactive=False, lines=2)
            
            # Conexión de eventos
            btn_csv.click(subir_csv_slp, inputs=[in_csv], outputs=[out_status])
            
            btn_manual.click(
                guardar_manual_slp, 
                inputs=[
                    man_fecha, man_hora, man_mpio, man_col, man_calle, man_ycalle, man_estado,
                    man_numero, man_entre, man_region, man_lat, man_lon, man_motivo
                ], 
                outputs=[
                    out_status, man_fecha, man_hora, man_mpio, man_col, man_calle, man_ycalle, man_estado,
                    man_numero, man_entre, man_region, man_lat, man_lon, man_motivo
                ]
            )

        # --- TAB 3: REPORTES ---
        with gr.Tab("Reportes"):
            gr.Markdown("### Exportar Datos")
            gr.Markdown("Puede descargar un reporte con los últimos 1000 datos usados para entrenar el modelo.")
            with gr.Row():
                btn_rep_xlsx = gr.Button("Descargar Excel")
                btn_rep_pdf = gr.Button("Descargar PDF")

            out_file = gr.File(label="Archivo Generado")
            
            # Usamos funciones lambda para pasar el parámetro de formato
            btn_rep_xlsx.click(lambda: generar_reporte_slp("xlsx"), outputs=out_file)
            btn_rep_pdf.click(lambda: generar_reporte_slp("pdf"), outputs=out_file)

        # --- TAB 4: ADMIN ---
        with gr.Tab("Gestión y Entrenamiento"):
            with gr.Row():
                btn_train = gr.Button("Re-entrenar Modelo")

            with gr.Row():
                out_log = gr.Textbox(label="Bitácora", interactive=False, lines=3)

            btn_train.click(reentrenar_modelo_slp, outputs=out_log)

if __name__ == "__main__":
    demo.queue().launch(theme=gr.themes.Soft())