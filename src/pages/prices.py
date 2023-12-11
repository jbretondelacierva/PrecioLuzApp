from dash import Dash, html, dcc, dash_table, callback
import plotly.graph_objs as go
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import requests
import pandas as pd
import dash
import pytz

dash.register_page(__name__)

import requests
import pandas as pd

def descargar_datos_precio_luz(fecha_inicio, fecha_fin, lang='es'):
    indicador = 'mercados/precios-mercados-tiempo-real'
    time_trunc = 'hour'

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    url = f'https://apidatos.ree.es/{lang}/datos/{indicador}?start_date={fecha_inicio}T00:00&end_date={fecha_fin}T23:59&time_trunc={time_trunc}'

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Esto provocará un error si el estado no es 200
        data = response.json()
        precios = pd.json_normalize(data['included'][0]['attributes']['values'])
        return precios
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")

    return pd.DataFrame()  # Devuelve un DataFrame vacío en caso de error


def calcular_precios(date):
    # Descargar datos de precios de la luz para el día seleccionado
    df_precio_luz = descargar_datos_precio_luz(date, date)

    # Verificar si el DataFrame está vacío
    if df_precio_luz.empty:
        print("No se pudieron obtener los datos para la fecha seleccionada.")
        return None

    # Convertir la columna 'datetime' a tipo datetime
    df_precio_luz['datetime'] = pd.to_datetime(df_precio_luz['datetime']).dt.tz_convert(pytz.FixedOffset(60))
    
    hora_actual = datetime.now(pytz.timezone("Europe/Madrid")).replace(minute=0, second=0, microsecond=0)

    # Filtrar los datos para obtener el precio más reciente hasta la hora actual
    df_hasta_hora_actual = df_precio_luz[df_precio_luz['datetime'] <= hora_actual]
    
    # Calcular el precio actual (último precio disponible)
    precio_actual = df_hasta_hora_actual['value'].iloc[-1]

    # Calcular el precio medio del día
    precio_medio = df_precio_luz['value'].mean()

    # Encontrar el precio más bajo y su hora correspondiente
    precio_minimo = df_precio_luz['value'].min()
    hora_precio_bajo = df_precio_luz[df_precio_luz['value'] == precio_minimo]['datetime'].iloc[0].strftime('%H:%M')

    # Encontrar el precio más alto y su hora correspondiente
    precio_maximo = df_precio_luz['value'].max()
    hora_precio_alto = df_precio_luz[df_precio_luz['value'] == precio_maximo]['datetime'].iloc[0].strftime('%H:%M')

    # Formatear los precios como cadenas con cinco decimales
    precios = {
        "precio_actual": f"{precio_actual:.2f}€/Wh",
        "precio_medio": f"{precio_medio:.2f}€/Wh",
        "precio_bajo": f"{precio_minimo:.2f}€/Wh",
        "hora_precio_bajo": hora_precio_bajo,
        "precio_alto": f"{precio_maximo:.2f}€/Wh",
        "hora_precio_alto": hora_precio_alto
    }

    return precios
# Definición de las tarjetas en el layout
tarjetas_precios = dbc.Row([
    dbc.Col(dbc.Card([dbc.CardBody([html.H5("Precio ahora mismo", className="card-title"), html.P("", className="card-text", id="precio-actual")])]), width=3),
    dbc.Col(dbc.Card([dbc.CardBody([html.H5("Precio medio del día", className="card-title"), html.P("", className="card-text", id="precio-medio")])]), width=3),
    dbc.Col(dbc.Card([dbc.CardBody([html.H5("Precio más bajo del día", className="card-title"), html.P("", className="card-text", id="precio-bajo"), html.P("", className="card-text", id="hora-precio-bajo")])]), width=3),
    dbc.Col(dbc.Card([dbc.CardBody([html.H5("Precio más alto del día", className="card-title"), html.P("", className="card-text", id="precio-alto"), html.P("", className="card-text", id="hora-precio-alto")])]), width=3),
], className="mb-4")


# Configura el DatePickerSingle
date_picker = dcc.DatePickerSingle(
    id='date-picker-range',
    min_date_allowed=datetime(2020, 1, 1),
    max_date_allowed=datetime.now(),
    initial_visible_month=datetime.now(),
    date=datetime.now().date()
)

layout = html.Div([
    html.H1('Precios Hoy', style={'textAlign': 'center'}),
    html.H4(id='fecha-seleccionada', style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div(date_picker, style={'textAlign': 'center', 'marginBottom': '20px'}),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='daily-graph')
        ], width=8),  # Tamaño de la columna para la gráfica del día
        dbc.Col([
            dash_table.DataTable(
                id='price-table',
                columns=[{"name": "Hora", "id": "Hora"}, {"name": "Precio (€/Wh)", "id": "Precio"}],
                style_table={'height': '400px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left', 'color': 'black'}
            )
        ], width=4)
    ]),
    tarjetas_precios
])


# Callback para actualizar la tabla de precios y los estilos condicionales
@callback(
    [Output('price-table', 'data'),
    Output('price-table', 'style_data_conditional')],
    Input('date-picker-range', 'date')
)
def update_price_table(date):
    # Descargar datos de precios de la luz para el día seleccionado
    df_precio_luz = descargar_datos_precio_luz(date, date)
     # Asegúrate de que 'datetime' exista en df_precio_luz
    if 'datetime' not in df_precio_luz.columns:
        print("La columna 'datetime' no se encuentra en el DataFrame.")
        return [], []
    # Convierte las columnas a tipos de datos correctos si es necesario
    df_precio_luz['datetime'] = pd.to_datetime(df_precio_luz['datetime']).dt.tz_convert(pytz.FixedOffset(60))
    df_precio_luz['Precio'] = df_precio_luz['value'].astype(float)
    
    # Calcula los percentiles para el día seleccionado
    percentil_bajo = df_precio_luz['Precio'].quantile(0.33)
    percentil_alto = df_precio_luz['Precio'].quantile(0.66)
    
    # Prepara los datos para la tabla
    df_precio_luz['Hora'] = df_precio_luz['datetime'].dt.strftime('%H:%M')
    table_data = df_precio_luz[['Hora', 'Precio']].to_dict('records')
    
    # Define los estilos condicionales basados en los percentiles calculados
    style_data_conditional=[
        {
            'if': {'column_id': 'Precio', 'filter_query': '{{Precio}} <= {}'.format(percentil_bajo)},
            'backgroundColor': '#3D9970',  # Verde para precios bajos
            'color': 'white',
        },
        {
            'if': {'column_id': 'Precio', 'filter_query': '{{Precio}} > {} && {{Precio}} <= {}'.format(percentil_bajo, percentil_alto)},
            'backgroundColor': '#FF851B',  # Naranja para precios medios
            'color': 'white',
        },
        {
            'if': {'column_id': 'Precio', 'filter_query': '{{Precio}} > {}'.format(percentil_alto)},
            'backgroundColor': '#FF4136',  # Rojo para precios altos
            'color': 'white',
        },
    ]
    
    # Retorna los datos y los estilos condicionales
    return table_data, style_data_conditional

# Callback para actualizar el gráfico de precios
@callback(
    Output('daily-graph', 'figure'),
    Input('date-picker-range', 'date')
)
def update_price_graph(date):

    # Descargar datos de precios de la luz
    df_precio_luz = descargar_datos_precio_luz(date, date)
    
    # Asegúrate de que 'datetime' y 'value' están en el DataFrame
    if 'datetime' not in df_precio_luz or 'value' not in df_precio_luz:
        print("Columnas necesarias no encontradas en el DataFrame.")
        return go.Figure()

    # Supongamos que definimos umbrales para los colores
    umbral_bajo = df_precio_luz['value'].quantile(0.33)
    umbral_alto = df_precio_luz['value'].quantile(0.66)

    fig_price = go.Figure()

    # Agregar segmentos de línea con colores diferentes
    for i in range(len(df_precio_luz) - 1):
        color = 'green' if df_precio_luz['value'].iloc[i] <= umbral_bajo else \
                'yellow' if df_precio_luz['value'].iloc[i] <= umbral_alto else \
                'red'
        
        fig_price.add_trace(go.Scatter(
            x=df_precio_luz['datetime'].iloc[i:i+2],
            y=df_precio_luz['value'].iloc[i:i+2],
            mode='lines',
            line=dict(color=color),
            showlegend=False
        ))

    # Obtener la fecha y hora actual
    now = datetime.now(pytz.timezone("Europe/Madrid")).replace(minute=0, second=0, microsecond=0)
    fecha_actual = datetime.strptime(date, '%Y-%m-%d')
    fecha_actual_con_hora_actual = datetime.combine(fecha_actual, now.time())

    # Añadir línea vertical para la hora actual
    fig_price.add_trace(go.Scatter(
        x=[fecha_actual_con_hora_actual, fecha_actual_con_hora_actual],
        y=[df_precio_luz['value'].min(), df_precio_luz['value'].max()],
        mode='lines',
        line=dict(color='black', dash='dash'),
        showlegend=False
    ))

    # Configuración de la trama y el papel
    fig_price.update_layout(
        title='Precios de la Electricidad',
        xaxis_title='Fecha',
        yaxis_title='Precio (€/Wh)',
        plot_bgcolor='rgb(255, 255, 255)',  # Fondo blanco
        paper_bgcolor='rgb(255, 255, 255)',  # Fondo del papel blanco
        font_color='black',  # Color de la fuente en negro
        xaxis=dict(showgrid=True, gridcolor='LightGray'),  # Cuadrícula suave para el eje X
        yaxis=dict(showgrid=True, gridcolor='LightGray')   # Cuadrícula suave para el eje Y
    )

    return fig_price

@callback(
    Output('fecha-seleccionada', 'children'),
    [Input('date-picker-range', 'date')]
)
def update_fecha_seleccionada(selected_date):
    if selected_date is not None:
        fecha = datetime.strptime(selected_date, '%Y-%m-%d')
        # Formateo manual
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        fecha_formateada = f"{dias[fecha.weekday()]}, {fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"
        return fecha_formateada
    return "Seleccione una fecha."


@callback(
    [
        Output("precio-actual", "children"),
        Output("precio-medio", "children"),
        Output("precio-bajo", "children"),
        Output("hora-precio-bajo", "children"),
        Output("precio-alto", "children"),
        Output("hora-precio-alto", "children")
    ],
    [Input("date-picker-range", "date")]
)
def actualizar_tarjetas(fecha_seleccionada):
    if fecha_seleccionada is not None:
        precios = calcular_precios(fecha_seleccionada)
        if precios:
            return precios["precio_actual"], precios["precio_medio"], precios["precio_bajo"], f"Entre las {precios['hora_precio_bajo']}", precios["precio_alto"], f"Entre las {precios['hora_precio_alto']}"
    return "", "", "", "", "", ""

# No olvides incluir este callback en tu aplicación junto con el resto del código.




