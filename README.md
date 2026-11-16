# Dashboard del tótem IoT de monitoreo fisiológico · EAFIT

Proyecto integrador de **Computación Física e Internet de las Cosas** (Universidad EAFIT).
Aplicación web en **Streamlit** que analiza mediciones simuladas de frecuencia cardíaca (BPM) y
saturación de oxígeno (SpO₂) registradas por un tótem con ESP32, lector NFC y sensor MAX30102.

> Todos los datos son **sintéticos**. No son mediciones reales ni información médica de estudiantes.
> El sensor del escenario es educativo y no es un dispositivo médico validado.

## Autor

Proyecto desarrollado de forma individual por: Maria José Rúa - mjruab@eafit.edu.co

## Enlaces

- Aplicación publicada: _pegar enlace de Streamlit Community Cloud_
- Video explicativo: _pegar enlace de YouTube_

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Contenido de la aplicación

- **Indicadores** (se actualizan con los filtros): mediciones, estudiantes distintos, BPM y SpO₂ promedio de las válidas, mediciones inválidas (cantidad y %).
- **Filtros** (barra lateral): rango de fechas, estudiante y estado de la medición (todas / válidas / inválidas).
- **Uso del tótem**: mediciones por día, mediciones por hora, mapa de calor día × hora, distribución de mediciones por estudiante y top 15.
- **Indicadores fisiológicos**: histogramas de BPM y SpO₂, evolución diaria del promedio, BPM por hora, dispersión BPM vs SpO₂ con atípicos.
- **Seguimiento individual**: identificador, número de mediciones, primera y última medición, evolución de BPM y SpO₂ y tabla del historial.
- **Calidad de datos**: válidas vs inválidas, % de inválidas por hora, calidad de señal por estado y resumen de chequeos.
- **Hallazgos y limitaciones**: cuatro hallazgos cuyas cifras se recalculan desde el CSV.

## Procesamiento de datos

1. Se lee el CSV con Pandas (`@st.cache_data`).
2. `timestamp` (UTC) se convierte a `America/Bogota`; de ahí se derivan fecha, hora y día de la semana.
3. Los indicadores fisiológicos usan solo `measurement_status == "valid"`.
4. Los valores atípicos se definen con el criterio estadístico 1.5×IQR sobre las mediciones válidas. No es un criterio clínico.

## Estructura del repositorio

```
app.py
requirements.txt
proyecto_integrador_eafit_max30102.csv
README.md
.gitignore
```

## Publicación en Streamlit Community Cloud

1. Sube el repositorio a GitHub.
2. En [share.streamlit.io](https://share.streamlit.io) crea una app nueva con el repositorio, la rama principal y `app.py` como archivo.
3. Abre el enlace público en una ventana de incógnito antes de entregarlo.
