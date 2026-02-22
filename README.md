# 🚔 Sistema de Predicción de Delitos - San Luis Potosí

Plataforma interactiva basada en Machine Learning para predecir zonas de alto riesgo de robo a casa habitación en San Luis Potosí. La aplicación genera mapas de calor probabilísticos, gestiona la ingesta de datos históricos y permite el reentrenamiento dinámico del modelo predictivo.

## ✨ Características Principales

* **Mapa de Calor Predictivo:** Utiliza un modelo `RandomForestClassifier` para estimar probabilidades de riesgo geolocalizadas según fecha y hora.
* **Gestión de Datos:** Ingesta masiva de datos mediante una base de datos MySQL, archivos CSV o captura de registros manuales.
* **Generación de Reportes:** Exportación de datos históricos en formatos PDF y Excel (`.xlsx`).
* **Reentrenamiento Dinámico:** Interfaz para actualizar el modelo de ML con los datos más recientes directamente desde la base de datos MySQL.

## 🏗️ Arquitectura del Proyecto

El proyecto está diseñado siguiendo el principio de **Separación de Responsabilidades (Separation of Concerns)**, aislando la interfaz gráfica de la lógica de negocio y la conexión a datos:

```text
prediccion-delitos-slp/
├── core/
│   ├── config.py         # Manejo seguro de rutas absolutas
│   └── database.py       # Conexión centralizada a MySQL (SQLAlchemy)
├── models/               # Modelo para la predicción del delito
|   ├── slp_coords.joblib
|   ├── slp_encoders.joblib
|   └── slp_model.joblib
├── services/
│   ├── data_service.py   # Lógica de ingesta de CSVs e inserciones manuales
│   ├── ml_service.py     # Carga, predicción y reentrenamiento del modelo (Scikit-Learn)
│   └── report_service.py # Generación de exportables
├── app.py                # Interfaz gráfica principal (Gradio)
├── requirements.txt      # Dependencias del proyecto
└── .env.example          # Plantilla de variables de entorno