
# Dashboard de Precios de Luz

## Descripción General
El Dashboard de Precios de Luz es una aplicación web interactiva y dinámica, diseñada para ofrecer análisis profundos y pronósticos sobre los precios de la electricidad. Esta herramienta es esencial para consumidores, analistas y entusiastas del sector energético que buscan comprender las tendencias y factores que influyen en el mercado eléctrico.

## Características

### Tendencias de Precios de Electricidad
- **Visualización Interactiva**: Gráficos y tablas interactivas que muestran el precio diario e histórico de la electricidad.
- **Filtrado por Fecha**: Opción para seleccionar dias específicos para un análisis más detallado.
- **Comparaciones de horas baja y alta demanda**: Análisis de las variaciones de precios en diferentes períodos.

### Predicciones de Precios
- **Modelos de Aprendizaje Automático**: Uso de algoritmos avanzados, incluyendo regresión lineal, redes neuronales y Prophet, para predecir futuros precios de la electricidad. Estos modelos consideran datos temporales clave como la hora y el día de la semana, además de las previsiones meteorológicas, que influyen directamente en la generación y demanda de energía.
- **Análisis de Tendencias**: Identificación de patrones y tendencias para anticipar cambios en los precios. Incorporación de datos meteorológicos de diversas localidades españolas para un análisis representativo de las condiciones climáticas. Experimentación con precios rezagados para optimizar las predicciones, equilibrando precisión y velocidad, crucial para interfaces web.
- **Manejo de Eventos Atípicos**: Reconocimiento de que el modelo puede tener limitaciones durante eventos atípicos como días festivos, donde los patrones de demanda y precios de la energía pueden variar significativamente.

### Análisis de Componentes
- **Desglose de Factores de Precio**: Análisis en profundidad de los componentes que afectan los precios, como la demanda y el uso de energías renovables.
- **Comparación con Mercados Energéticos**: Comparativas con otros mercados para entender el comportamiento del mercado local en un contexto más amplio.
- **Demanda Real y Programada en Tiempo Real**: Visualización de la demanda eléctrica actual y prevista, proporcionando una comprensión clara de las necesidades energéticas en tiempo real.
- **Impacto de las Energías Renovables**: Visualización de cómo el uso de energías renovables puede contribuir a precios más bajos.

## Instalación
1. Clona el repositorio a tu máquina local.
2. Instala las dependencias necesarias.

## Uso
Para iniciar la aplicación, ejecuta:
```bash
python app.py
```
Navega al dashboard en `http://127.0.0.1:8050`.

## Estructura del Proyecto
- `app.py`: Archivo principal que ejecuta la aplicación Dash.
- `components.py`: Módulo para el análisis de los componentes que afectan los precios de la electricidad.
- `predictions.py`: Módulo para la generación de predicciones de precios utilizando modelos de aprendizaje automático.
- `prices.py`: Módulo para la obtención y visualización de los datos de precios de la electricidad.

