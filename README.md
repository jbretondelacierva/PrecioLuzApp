
# Dashboard de Precios de Luz

## Descripción General
El Dashboard de Precios de Luz es una aplicación web interactiva y dinámica, diseñada para ofrecer análisis profundos y pronósticos sobre los precios de la electricidad. Esta herramienta es esencial para consumidores, analistas y entusiastas del sector energético que buscan comprender las tendencias y factores que influyen en el mercado eléctrico.

## Características

### Tendencias de Precios de Electricidad
- **Visualización Interactiva**: Gráficos y tablas interactivas que muestran los precios históricos de la electricidad.
- **Filtrado por Fecha**: Opción para seleccionar rangos de fechas específicos para un análisis más detallado.
- **Comparaciones Diarias, Semanales y Mensuales**: Análisis de las variaciones de precios en diferentes períodos.

### Predicciones de Precios
- **Modelos de Aprendizaje Automático**: Uso de algoritmos avanzados para predecir futuros precios de la electricidad.
- **Análisis de Tendencias**: Identificación de patrones y tendencias para anticipar cambios en los precios.
- **Alertas de Precios**: Notificaciones sobre pronósticos de precios altos o bajos, permitiendo una planificación eficiente.

### Análisis de Componentes
- **Desglose de Factores de Precio**: Análisis en profundidad de los componentes que afectan los precios, como la demanda, la oferta y los eventos del mercado.
- **Visualización de Datos en Tiempo Real**: Integración de datos en tiempo real para un análisis actualizado y relevante.
- **Comparación con Mercados Energéticos**: Comparativas con otros mercados para entender el comportamiento del mercado local en un contexto más amplio.

## Instalación
1. Clona el repositorio a tu máquina local.
2. Instala las dependencias necesarias con `pip install -r requirements.txt`.

## Uso
Para iniciar la aplicación, ejecuta:
```bash
python app.py
```
Navega al dashboard en `http://localhost:8050`.

## Estructura del Proyecto
- `app.py`: Archivo principal que ejecuta la aplicación Dash.
- `components.py`: Módulo para el análisis de los componentes que afectan los precios de la electricidad.
- `predictions.py`: Módulo para la generación de predicciones de precios utilizando modelos de aprendizaje automático.
- `prices.py`: Módulo para la obtención y visualización de los datos de precios de la electricidad.

## Tecnologías
- **Dash**: Framework de Python para aplicaciones web analíticas.
- **Plotly**: Para gráficos interactivos y visualizaciones.
- **Pandas**: Manejo y análisis de datos.
- **Requests**: Realización de peticiones HTTP.

## Contribuir
Las contribuciones son bienvenidas. Consulta las pautas de contribución para más información.

## Licencia
Este proyecto está bajo la licencia [Nombre de Tu Licencia].
