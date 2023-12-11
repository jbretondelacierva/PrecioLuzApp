from dash import Dash, html, dcc, dash_table, callback
import plotly.graph_objs as go
from datetime import datetime, timedelta
from dash.dependencies import Input, Output
import plotly.express as px
import requests
import pandas as pd
import dash
import plotly.figure_factory as ff

dash.register_page(__name__)
# Aquí podrías definir tus figuras de Plotly para el análisis de componentes
# Este es solo un ejemplo vacío
def download_ree(indicador,fecha_inicio,fecha_fin,time_trunc='day'):
   
    headers = {'Accept': 'application/json',
               'Content-Type': 'applic<ation/json',
               'Host': 'apidatos.ree.es'}
    
    end_point = 'https://apidatos.ree.es/es/datos/'
    
    lista=[]
    url = f'{end_point}{indicador}?start_date={fecha_inicio}T00:00&end_date={fecha_fin}T23:59&\
    time_trunc={time_trunc}'
    print (url)
    
    response = requests.get(url, headers=headers).json()
    
    return pd.json_normalize(data=response['included'], 
                                   record_path=['attributes','values'], 
                                   meta=['type',['attributes','type' ]], 
                                   errors='ignore')
def download_esios(indicadores, fecha_inicio, fecha_fin,time_trunc='day'):
    
    # preparamos la cabecera a insertar en la llamada. Vease la necesidad de disponer el token de esios
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'x-api-key': '0d9a4cff670787f2e537d9ae3a39f484982532723c61106f4639c16d3c565538'
    }
    
    # preparamos la url básica a la que se le añadiran los campos necesarios 
    
    end_point = 'https://api.esios.ree.es/indicators'
    
    # El procedimiento es sencillo: 
    # a) por cada uno de los indicadores configuraremos la url, según las indicaciones de la documentación.
    # b) Hacemos la llamada y recogemos los datos en formato json.
    # c) Añadimos la información a una lista
    
    lista=[]

    for indicador in indicadores:
        url = f'{end_point}/{indicador}?start_date={fecha_inicio}T00:00&\
        end_date={fecha_fin}T23:59&time_trunc={time_trunc}'
        print (url)
        response = requests.get(url, headers=headers).json()
        lista.append(pd.json_normalize(data=response['indicator'], record_path=['values'], meta=['name','short_name'], errors='ignore'))

    # Devolvemos como salida de la función un df fruto de la concatenación de los elemenos de la lista
    # Este procedimiento, con una sola concatenación al final, es mucho más eficiente que hacer múltiples 
    # concatenaciones.
    
    return pd.concat(lista, ignore_index=True )

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

def calcular_porcentaje_renovables(start_date, end_date):
    # Suponiendo que download_esios es una función existente para descargar los datos
    datos_raw = download_ree('generacion/estructura-generacion', start_date, end_date)
    renewable_sources = [
            'Hidráulica', 'Turbinación bombeo', 'Eólica', 'Solar fotovoltaica',
            'Solar térmica', 'Hidroeólica', 'Otras renovables', 'Residuos renovables'
        ]
    # Procesamiento de los datos
    datos = (datos_raw.assign(fecha=lambda df_: pd.to_datetime(df_['datetime'], utc=True)
                          .dt.tz_convert('Europe/Madrid')
                          .dt.tz_localize(None))
                  .query('type in @renewable_sources')
                  .drop(['attributes.type', 'datetime'], axis=1)
                  .rename(columns={'value': 'valor', 'type': 'tipo', 'value': 'generacion'})
                  [['fecha', 'tipo', 'generacion', 'percentage']]
                 )   

    # Filtrar datos de fuentes renovables y calcular el total por fecha
    datos_renovables = datos[datos['tipo'].isin(renewable_sources)]
    total_renovable = datos_renovables.groupby('fecha')['percentage'].sum().reset_index()

    print(renewable_sources)
    return total_renovable



# Añadir DatePickerRange, Dropdown y Graph al layout
layout = html.Div([
    html.H1('Análisis de Componentes', style={'textAlign': 'center'}),
    dcc.DatePickerRange(
        id='date-picker-range',
        start_date=(datetime.today() - timedelta(days=15)).date(),
        end_date=datetime.today().date(),
        style={'marginBottom': '10px'}  # Añadir un margen inferior
    ),
    dcc.Dropdown(
        id='type-dropdown',
        options=[
            {'label': tipo, 'value': tipo} for tipo in [
                'Hidráulica', 'Turbinación bombeo', 'Nuclear', 'Carbón',
                'Motores diésel', 'Turbina de gas', 'Turbina de vapor',
                'Ciclo combinado', 'Hidroeólica', 'Eólica', 'Solar fotovoltaica',
                'Solar térmica', 'Otras renovables', 'Cogeneración',
                'Residuos no renovables', 'Residuos renovables'
            ]
        ],
        value=['Nuclear', 'Solar fotovoltaica', 'Hidráulica', 'Eólica'],
        multi=True,
        style={'color': 'black'} 
    ),
    dcc.Graph(id='generation-graph'),
    dcc.Graph(id='price-graph'),
    html.P([
        "Vemos el impacto de las Energías Renovables en el precio de la electricidad, donde se puede apreciar una correlacion negativa. Esto nos da entender que el uso de Energías Renovables puede contribuir a precios más bajos."
        ]),
    dcc.Graph(id='my-plotly-graph'),
    html.P([
        "La gráfica muestra la demanda eléctrica y cómo disminuye significativamente los fines de semana, reflejando menor actividad industrial y comercial. Existe una correlación evidente entre la demanda y los precios: altas demandas suelen elevar los precios, mientras que los fines de semana, con demandas más bajas, los precios tienden a caer. Este patrón es clave para entender y prever los cambios en los precios de la electricidad."
        ]),
    dcc.Graph(id='correlation-graph')

])


@callback(
    Output('generation-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('type-dropdown', 'value')]
)
def update_graph(start_date, end_date, generation_types):
    # Llamada a la función download_ree
    raw = download_ree('generacion/estructura-generacion', start_date, end_date)
    
    # Procesamiento de los datos
    generacion = (raw
                  .assign(fecha=lambda df_: pd.to_datetime(df_['datetime'], utc=True)
                          .dt.tz_convert('Europe/Madrid')
                          .dt.tz_localize(None))
                  .query('type in @generation_types')
                  .drop(['attributes.type', 'datetime'], axis=1)
                  .rename(columns={'value': 'valor', 'type': 'tipo', 'value': 'generacion'})
                  [['fecha', 'tipo', 'generacion', 'percentage']]
                 )

    # Crear la figura con Plotly Express
    fig = px.bar(
        generacion,
        x='fecha',
        y='percentage',
        color='tipo',
        title='Evolución de diferentes tecnologías de generación',
        labels={'percentage': 'Porcentaje'}
    )


    return fig

@callback(
    Output('price-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_price_graph(start_date, end_date):
    # Descargar y procesar datos de energía renovable
    datos_renovables = calcular_porcentaje_renovables(start_date, end_date)
    print(datos_renovables.columns)
    # Descargar y procesar datos del precio de la luz
    precios_luz = descargar_datos_precio_luz(start_date, end_date)

    # Crear el gráfico
    fig = go.Figure()
    # Añadir datos de energía renovable
    if not datos_renovables.empty:
        fig.add_trace(go.Scatter(
            x=datos_renovables['fecha'],
            y=datos_renovables['percentage'],
            mode='lines',
            name='Porcentaje Renovable',
            yaxis='y1',
            line=dict(color='green')
        ))

    # Añadir datos del precio de la luz
    if not precios_luz.empty:
        fig.add_trace(go.Scatter(
            x=precios_luz['datetime'],
            y=precios_luz['value'],
            mode='lines',
            name='Precio Luz',
            yaxis='y2',
            line=dict(color='blue')
        ))

    # Configurar la apariencia del gráfico
    fig.update_layout(
        title_text='Porcentaje de Energía Renovable y Precio de la Luz',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, color='black'),
        yaxis=dict(title='Porcentaje Renovable', color='green', side='left'),
        yaxis2=dict(title='Precio Luz (€/Wh)', color='blue', side='right', overlaying='y'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(color='black')
    )

    return fig


@callback(
    Output('my-plotly-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_my_plotly_graph(start_date, end_date):
    # Suponiendo que download_esios es una función existente para descargar los datos
    datos_raw = download_esios([544, 545, 1293], start_date, end_date, time_trunc='hour')

    # Procesamiento de los datos
    datos = (datos_raw
             .assign(fecha=lambda df_: pd.to_datetime(df_['datetime'], utc=True)
                     .dt.tz_convert('Europe/Madrid')
                     .dt.tz_localize(None))
             .drop(['datetime', 'datetime_utc', 'tz_time', 'geo_id', 'geo_name', 'short_name'], axis=1)
             .loc[:, ['fecha', 'name', 'value']]
             )

    # Crear el gráfico
    fig = go.Figure()

    # Colores para las líneas
    colores = {'Categoria1': 'violet', 'Categoria2': 'green', 'Categoria3': 'orange'}

    # Agregar las líneas
    for name, group in datos.groupby('name'):
        fig.add_trace(go.Scatter(
            x=group['fecha'],
            y=group['value'],
            mode='lines',
            name=name,
            line=dict(color=colores.get(name))
        ))

    # Convertir fechas a objetos datetime de Python y filtrar para las 12 del mediodía
    fechas_filtradas = [pd.to_datetime(fecha) for fecha in datos['fecha'].unique() if pd.to_datetime(fecha).hour == 0]

    # Configurar la apariencia del gráfico
    fig.update_layout(
        title_text='Demanda prevista vs Demanda programada vs Demanda real',
        plot_bgcolor='white',  # Área del gráfico blanca
        paper_bgcolor='white',  # Fondo del gráfico blanco
        xaxis=dict(
            tickvals=fechas_filtradas,
            ticktext=[fecha.strftime('%d-%b') for fecha in fechas_filtradas],
            tickangle=-45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='LightGray',
            tickformat=',.0f'
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(color='black')
    )

    # Agregar color de fondo para los fines de semana
    for fecha in fechas_filtradas:
        if fecha.weekday() in [5, 6]:  # 5: Sábado, 6: Domingo
            fig.add_vrect(
                x0=fecha, x1=fecha + pd.Timedelta(days=1),
                fillcolor="LightGray", opacity=0.4,
                layer="below", line_width=0,
            )

    return fig

@callback(
    Output('correlation-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_correlation_graph(start_date, end_date):
    # Descargar y procesar datos de generación
    raw = download_ree('generacion/estructura-generacion', start_date, end_date)
    generacion = (raw
                  .assign(fecha=lambda df_: pd.to_datetime(df_['datetime'], utc=True)
                          .dt.tz_convert('Europe/Madrid')
                          .dt.tz_localize(None))
                  .drop(['attributes.type', 'datetime'], axis=1)
                  .rename(columns={'value': 'generacion', 'type': 'tipo'})
                  [['fecha', 'tipo', 'generacion']]
                 )
    generacion_pivot = generacion.pivot_table(index='fecha', columns='tipo', values='generacion', aggfunc='sum').reset_index()

    # Descargar y procesar datos del precio de la luz
    datos_precio_luz = descargar_datos_precio_luz(start_date, end_date)
    datos_precio_luz['fecha'] = pd.to_datetime(datos_precio_luz['datetime']).dt.date
    precio_medio_diario = datos_precio_luz.groupby('fecha')['value'].mean().reset_index()
    generacion_pivot.reset_index(drop=True, inplace=True)
    generacion_pivot.drop(columns='Generación total', inplace=True)
    generacion_pivot['fecha'] = pd.to_datetime(generacion_pivot['fecha']).dt.date
    # Fusionar los datos de generación con los datos del precio de la luz
    datos_combinados = pd.merge(generacion_pivot, precio_medio_diario, on='fecha')
    # Calcular la correlación
    correlacion = datos_combinados.corr()

    # Crear una tabla de correlación con Plotly
    fig = ff.create_annotated_heatmap(
        z=correlacion.values,
        x=correlacion.columns.tolist(),
        y=correlacion.index.tolist(),
        annotation_text=correlacion.round(2).values,
        colorscale='Viridis'
    )
    fig.update_layout(
        title_text='Correlación entre Tipos de Generación de Energía y Precio Medio Diario de la Luz(en el intervalo seleccionado)',
        xaxis=dict(tickangle=-45),
        yaxis=dict(ticks=''),
        font=dict(color='black')
    )

    return fig
