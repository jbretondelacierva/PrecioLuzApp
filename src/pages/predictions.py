from dash import Dash, html, dcc, dash_table, callback
import plotly.graph_objs as go
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import requests
import pandas as pd
import dash
import dash
from joblib import load
dash.register_page(__name__)

api_key = '7f1ac9e2a6deeea5fbf2dbb18d570a7e'

def obtener_datos_meteorologicos(latitud, longitud, api_key):
    """
    Obtiene datos meteorológicos por hora para una ubicación específica.
    """
    base_url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {
        'lat': latitud,
        'lon': longitud,
        'appid': api_key,
        'units': 'metric',
        'exclude': 'current,minutely,daily,alerts'
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        hourly_data = data.get('hourly', [])
        return pd.DataFrame(hourly_data)
    else:
        print(f"Error en la solicitud: {response.status_code}")
        return pd.DataFrame()
def descargar_datos_precio_luz(start_date, end_date, lang='es'):
    """
    Descarga datos de precios de la electricidad desde apidatos.ree.es.

    Args:
    fecha_inicio (str): Fecha de inicio en formato 'YYYY-MM-DD'.
    fecha_fin (str): Fecha de fin en formato 'YYYY-MM-DD'.
    lang (str): Idioma de la respuesta ('es' para español, 'en' para inglés).

    Returns:
    DataFrame: Un DataFrame de pandas con los datos del precio de la electricidad.
    """
    indicador = 'mercados/precios-mercados-tiempo-real'
    time_trunc = 'hour'  # Cambiado de 'day' a 'hour' según el error recibido

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    url = f'https://apidatos.ree.es/{lang}/datos/{indicador}?start_date={start_date}T00:00&end_date={end_date}T23:59&time_trunc={time_trunc}'
    print(url)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        # Asegúrate de ajustar la siguiente línea según la estructura real de los datos
        precios = pd.json_normalize(data['included'][0]['attributes']['values'])
        return precios
    else:
        print(f"Error en la solicitud: {response.status_code}")
        return pd.DataFrame()  # Devuelve un DataFrame vacío en caso de error
def descargar_datos_mensuales(fecha_inicio, fecha_fin):
    precios_mensuales = pd.DataFrame()
    while fecha_inicio < fecha_fin:
        # Asegúrate de que el período de solicitud no exceda 31 días
        fecha_fin_mes = min(fecha_inicio + timedelta(days=20), fecha_fin)

        precios = descargar_datos_precio_luz(fecha_inicio.date(), fecha_fin_mes.date())
        precios_mensuales = pd.concat([precios_mensuales, precios])

        # Avanza al siguiente mes
        fecha_inicio = fecha_fin_mes
    return precios_mensuales

ubicaciones = {
    'Burgos': {'latitud': 42.343993, 'longitud': -3.696906},
    'Segovia': {'latitud': 40.942903, 'longitud': -4.108807},
    'A Coruña': {'latitud': 43.362344, 'longitud': -8.411540},
    'Teruel': {'latitud': 40.345688, 'longitud': -1.106434},
    'Ciudad Real': {'latitud': 38.984829, 'longitud': -3.927377},
    'Zaragoza': {'latitud': 41.648823, 'longitud': -0.889085},
    'Jaén': {'latitud': 37.779594, 'longitud': -3.784906}
}
# DataFrame para consolidar la información
predicciones_tiempo = pd.DataFrame()

for ciudad, coords in ubicaciones.items():
    df_temporal = obtener_datos_meteorologicos(coords['latitud'], coords['longitud'], api_key)
    df_temporal['datetime'] = pd.to_datetime(df_temporal['dt'], unit='s')
    df_temporal = df_temporal[['datetime', 'wind_speed', 'wind_deg', 'temp']]
    
    # Renombrar las columnas
    df_temporal.rename(columns={
        'wind_speed': f'{ciudad}_wind_speed_10m',
        'wind_deg': f'{ciudad}_wind_direction_10m',
        'temp': f'{ciudad}_temperature_2m',
    }, inplace=True)
    
    if predicciones_tiempo.empty:
        predicciones_tiempo = df_temporal
    else:
        predicciones_tiempo = pd.merge(predicciones_tiempo, df_temporal, on='datetime', how='outer')

# Añadir columnas de hora y día de la semana
predicciones_tiempo['hora'] = predicciones_tiempo['datetime'].dt.hour
predicciones_tiempo['dia_semana'] = predicciones_tiempo['datetime'].dt.dayofweek

# Convertir 'hora' y 'dia_semana' a variables categóricas
for hora in range(24):
    predicciones_tiempo[f'hora_{hora}'] = (predicciones_tiempo['hora'] == hora).astype(int)

for dia in range(7):
    predicciones_tiempo[f'dia_semana_{dia}'] = (predicciones_tiempo['dia_semana'] == dia).astype(int)

# Eliminar las columnas originales 'hora' y 'dia_semana'
predicciones_tiempo.drop(['hora', 'dia_semana'], axis=1, inplace=True)

# Calcula las fechas de inicio y fin para los últimos 5 años
fecha_fin = datetime.now()
#fecha_inicio = fecha_fin.replace(year=fecha_fin.year - 5)
fecha_inicio = fecha_fin - timedelta(days=3)


# Descarga los datos en segmentos mensuales
precios = descargar_datos_mensuales(fecha_inicio, fecha_fin)
precios_copia = precios
precios_copia['datetime'] = pd.to_datetime(precios['datetime'], utc=True)

futuro = predicciones_tiempo.copy()
futuro_para_prediccion = futuro.drop('datetime', axis=1)

model = load('modelo_regresion_lineal.joblib')

predicciones = model.predict(futuro_para_prediccion)
futuro['value'] = predicciones

# Añadir una columna para identificar los datos de entrenamiento y las predicciones
precios_copia['tipo'] = 'Entrenamiento'
futuro['tipo'] = 'Predicción'

# Combinar los datos de entrenamiento y las predicciones
df_combinado = pd.concat([precios_copia, futuro])

futuro_RN = predicciones_tiempo.copy()
futuro_para_prediccion_RN = futuro_RN.drop('datetime', axis=1)
from sklearn.preprocessing import StandardScaler
modelo = load('modelo_redes_neuronales.joblib')
y_pred = modelo.predict(futuro_para_prediccion_RN)

# Convertir las predicciones a un DataFrame
predicciones_df = pd.DataFrame(y_pred, columns=['Predicción'])

# Asegurarse de que el DataFrame 'futuro_RN' tenga el mismo número de filas que 'predicciones_df'
futuro_RN_RN = futuro_RN.reset_index(drop=True)[:len(predicciones_df)]

# Añadir las predicciones al DataFrame 'futuro_RN'
futuro_RN['value'] = predicciones_df['Predicción']

# Asumiendo que 'datos_entrenamiento' es tu DataFrame original con las columnas 'datetime' y 'value'
futuro_RN['tipo'] = 'Predicción_RN'

# Combinar los datos de entrenamiento y las predicciones
df_combinado = pd.concat([df_combinado, futuro_RN[['datetime', 'value', 'tipo']]])

###############################
layout = html.Div([
    html.H1('Predicciones de Precios', style={'textAlign': 'center'}),
        
    # Componente para elegir qué predicciones mostrar
    dcc.Checklist(
        id='selector_prediccion',
        options=[
            {'label': 'Mostrar Predicciones Regresión Lineal', 'value': 'pred_RL'},
            {'label': 'Mostrar Predicciones Red Neuronal', 'value': 'pred_RN'}
        ],
        value=['pred_RL', 'pred_RN']  # Valores predeterminados
    ),

    dcc.Graph(id='grafico_predicciones', style={'height': '600px'}),  # Aumentar altura de la gráfica
    # Descripción de los modelos y la lógica de las variables
    html.Div([
        html.P([
            "Los modelos de predicción de precios han sido entrenados utilizando datos de los días de la semana, horas del día, temperatura, y viento de varias ubicaciones en España. Las ciudades seleccionadas para la recopilación de datos meteorológicos son Burgos, Segovia, A Coruña, Teruel, Ciudad Real, Zaragoza y Jaén. Estas ubicaciones ofrecen una representación diversa de las condiciones climáticas en España y su impacto en la generación de energías renovables."
        ]),
        html.P([
            "Un factor clave en la generación de energía renovable es el viento, ya que mayores velocidades de viento favorecen la producción de energía eólica. Además, la demanda de energía varía con las estaciones: en invierno aumenta con el frío, mientras que en verano disminuye. Por esta razón, también consideramos el factor mes en nuestros modelos."
        ]),
        html.P([
            "Para estos modelos, nos hemos centrado en datos de los últimos 3 meses. Observamos que, debido a la variabilidad impredecible del precio de la energía, extender el periodo de análisis resultaba en una disminución significativa del coeficiente de determinación (R²) de nuestros modelos."
        ])
    ], style={'marginBottom': '20px', 'marginTop': '20px'}),
    # Agregar aquí más gráficos según necesites
    html.H3('Modelos con Prophet y Arima en proceso', style={'textAlign': 'center'}),

])
########################
# Callback para actualizar el gráfico de predicciones
@callback(
    Output('grafico_predicciones', 'figure'),
    [Input('selector_prediccion', 'value')]  # Se activa con el cambio en el selector
)
def update_grafico_predicciones(opciones_prediccion):
    # Crear figura de Plotly
    fig = go.Figure()

    # Siempre añadir traza para los datos de entrenamiento
    fig.add_trace(go.Scatter(
        x=df_combinado[df_combinado['tipo'] == 'Entrenamiento']['datetime'],
        y=df_combinado[df_combinado['tipo'] == 'Entrenamiento']['value'],
        mode='lines',
        name='Entrenamiento'
    ))

    # Añadir trazas para las predicciones seleccionadas
    if 'pred_RL' in opciones_prediccion:
        fig.add_trace(go.Scatter(
            x=df_combinado[df_combinado['tipo'] == 'Predicción']['datetime'],
            y=df_combinado[df_combinado['tipo'] == 'Predicción']['value'],
            mode='lines',
            name='Predicción RL'
        ))
    if 'pred_RN' in opciones_prediccion:
        fig.add_trace(go.Scatter(
            x=df_combinado[df_combinado['tipo'] == 'Predicción_RN']['datetime'],
            y=df_combinado[df_combinado['tipo'] == 'Predicción_RN']['value'],
            mode='lines',
            name='Predicción RN'
        ))

    # Actualizar el layout del gráfico
    fig.update_layout(
        title='Valor de Entrenamiento vs Predicciones',
        xaxis_title='Tiempo',
        yaxis_title='Valor',
        legend_title='Tipo'
    )

    return fig

