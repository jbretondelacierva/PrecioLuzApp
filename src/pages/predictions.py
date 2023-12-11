from dash import Dash, html, dcc, dash_table, callback
import plotly.graph_objs as go
from datetime import datetime, timedelta
import locale
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import requests
import pandas as pd
import dash
import dash
from joblib import load
from prophet import Prophet
from sklearn.preprocessing import StandardScaler

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
df_combinado = precios.copy()
df_combinado['datetime'] = pd.to_datetime(precios['datetime'], utc=True)
df_combinado['tipo'] = 'Entrenamiento'
futuro = predicciones_tiempo.copy()
futuro_para_prediccion = futuro.drop('datetime', axis=1)


try:
    model = load('modelo_regresion_lineal.joblib')

    predicciones = model.predict(futuro_para_prediccion)
    futuro['value'] = predicciones

    # Añadir una columna para identificar los datos de entrenamiento y las predicciones
    futuro['tipo'] = 'Predicción'

    # Combinar los datos de entrenamiento y las predicciones
    df_combinado = pd.concat([df_combinado, futuro])

except Exception as e:
    print(e)

try:
    futuro_RN = predicciones_tiempo.copy()
    futuro_para_prediccion_RN = futuro_RN.drop('datetime', axis=1)
    print("molo")
    modelo = load('modelo_redes_neuronales.joblib')
    print("adioas")
    y_pred = modelo.predict(futuro_para_prediccion_RN)
    print(y_pred)
    # Convertir las predicciones a un DataFrame
    predicciones_df = pd.DataFrame(y_pred, columns=['Predicción'])
    print("holaaa0")
    # Asegurarse de que el DataFrame 'futuro_RN' tenga el mismo número de filas que 'predicciones_df'
    futuro_RN_RN = futuro_RN.reset_index(drop=True)[:len(predicciones_df)]
    print("holaaa")
    # Añadir las predicciones al DataFrame 'futuro_RN'
    futuro_RN['value'] = predicciones_df['Predicción']

    # Asumiendo que 'datos_entrenamiento' es tu DataFrame original con las columnas 'datetime' y 'value'
    futuro_RN['tipo'] = 'Predicción_RN'

    # Combinar los datos de entrenamiento y las predicciones
    df_combinado = pd.concat([df_combinado, futuro_RN[['datetime', 'value', 'tipo']]])

except Exception as e:
    print(e)
    print("porque me pasan estas cosas")

preciosProphet = descargar_datos_mensuales(datetime.now() - timedelta(days=90), fecha_fin)
preciosProphet['datetime'] = pd.to_datetime(preciosProphet['datetime'], utc=True)

preciosProphet['datetime'] = preciosProphet['datetime'].dt.tz_localize(None)

df_prophet = preciosProphet[['datetime', 'value']].rename(columns={'datetime': 'ds', 'value': 'y'})
modelo_prophet = Prophet()
modelo_prophet.fit(df_prophet)


# Crear DataFrame futuro para las predicciones
futuro_prophet = modelo_prophet.make_future_dataframe(periods=48, freq='H')
try:
    ultimo_valor_datetime = futuro_RN['datetime'].iloc[-1]
    futuro_prophet = futuro_prophet[futuro_prophet['ds'] <= ultimo_valor_datetime]
    ultimo_valor_datetime= futuro_RN['datetime'].iloc[0]
    futuro_prophet = futuro_prophet[ futuro_prophet['ds'] >= ultimo_valor_datetime]  # Asegúrate de que solo contenga fechas futuras
except Exception as e:
    print(e)

# Realizar predicciones
predicciones_prophet = modelo_prophet.predict(futuro_prophet)


###############################
layout = html.Div([
    html.H1('Predicciones de Precios', style={'textAlign': 'center'}),
        
    # Componente para elegir qué predicciones mostrar
    dcc.Checklist(
        id='selector_prediccion',
        options=[
            {'label': 'Mostrar Predicciones Regresión Lineal', 'value': 'pred_RL'},
            {'label': 'Mostrar Predicciones Red Neuronal', 'value': 'pred_RN'},
            {'label': 'Mostrar Predicciones Prophet', 'value': 'pred_Prophet'}  # Añadir esta línea
        ],
        value=['pred_RL', 'pred_RN', 'pred_Prophet']  # Incluir 'pred_Prophet' aquí
    ),


    dcc.Graph(id='grafico_predicciones', style={'height': '600px'}),  # Aumentar altura de la gráfica
        # Descripción de los modelos y la lógica de las variables
        html.P([
            "En el desarrollo de mis modelos de predicción de precios, he priorizado datos temporales como la hora y el día de la semana, clave para comprender los patrones de consumo energético. Las previsiones meteorológicas han sido esenciales, influenciando directamente en la generación y demanda de energía. Este enfoque me ha permitido afinar las predicciones, maximizando su relevancia y precisión."
        ]),
        html.P([
            "La integración de datos meteorológicos de diversas localidades españolas, tales como Burgos, Segovia, A Coruña, Teruel, entre otras, ha aportado un análisis detallado y representativo de las condiciones climáticas del país. Este análisis se ha limitado intencionalmente a los últimos 90 días para enfocarse en tendencias recientes y minimizar la distorsión por variaciones estacionales históricas."
        ]),
        html.P([
            "Una faceta interesante de mi trabajo ha sido experimentar con precios rezagados de 2, 3 y 7 días, aunque los resultados mostraron mejoras marginales. Esto se debe, en parte, a que un lag ideal sería cercano a una hora, cosa que no era posible ya que mis predicciones eran de dos dias(tambien por las predicciones meteorologicas). Asi mismo, el modelo Prophet, solo lo aplico a predicciones de dos días, para poder compararlo bien con los otros modelos, no arrastrar errores, balanceando precisión y velocidad, especialmente crucial para interfaces web. En comparación, el modelo ARIMA, aunque profundo en su análisis, fue descartado por su prolongado tiempo de procesamiento."
        ]),
        html.P([
            "El desafío más notable ha sido la variabilidad en las predicciones durante eventos atípicos, como los días festivos, donde se observan cambios significativos en la demanda y precios de la energía. La elección de una ventana de análisis de 90 días ha demostrado ser un equilibrio perfecto entre precisión y practicidad, evitando la sobrecomplicación y el riesgo de sobreajuste. En particular, tanto la Red Neuronal como la Regresión Lineal se han beneficiado de este enfoque, mientras que Prophet ha demostrado ser excepcionalmente adecuado para la interfaz web, gracias a su eficiencia en la generación de predicciones a corto plazo."
        ], style={'marginBottom': '20px', 'marginTop': '20px'})
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

    if 'pred_Prophet' in opciones_prediccion:
        fig.add_trace(go.Scatter(
            x=predicciones_prophet['ds'],
            y=predicciones_prophet['yhat'],
            mode='lines',
            name='Predicción Prophet'
        ))

    # Actualizar el layout del gráfico
    fig.update_layout(
        title='Valor de Entrenamiento vs Predicciones',
        xaxis_title='Tiempo',
        yaxis_title='Valor',
        legend_title='Tipo'
    )

    return fig

