import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import requests

# Suponiendo que la función download_ree ya está definida como la proporcionaste
def download_ree(indicador,fecha_inicio,fecha_fin,time_trunc='day'):
    """
    Descarga datos desde apidatos.ree.es entre dos fechas determinadas 
    
    Parameters
    ----------
    
    indicador : str
        Texto con el indicador del end point del que queremo bajar la información
        
    fecha_inicio : str
        Fecha con formato %Y-%M-%d, que indica la fecha desde la que se quiere bajar los datos.
        Ejemplo 2022-10-30, 30 Octubre de 2022.
    
    fecha_fin : str
        Fecha con formato %Y-%M-%d, que indica la fecha hasta la que se quiere bajar los datos.
        Ejemplo 2022-10-30, 30 Octubre de 2022.
        
    time_trunc : str, optional
        Campo adicional que nos permite elegir la granularidad de los datos que queremos bajar.
        Hour, Day, Month...dependiendo del end point se aplicará o no esta orden
        
    Returns
    -------
    DataFrame
        Dataframe de pandas con los datos solicitados
    
    """
    
    
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
# Inicializar la aplicación Dash
app = dash.Dash(__name__)

# Layout de la aplicación
app.layout = html.Div([
    html.H1("Dashboard de Generación de Electricidad"),
    dcc.DatePickerRange(
        id='date-picker-range',
        start_date=(datetime.today() - timedelta(days=7)).date(),
        end_date=datetime.today().date()
    ),
    dcc.Dropdown(
        id='type-dropdown',
        options=[
            {'label': 'Nuclear', 'value': 'Nuclear'},
            {'label': 'Solar fotovoltaica', 'value': 'Solar fotovoltaica'},
            {'label': 'Eólica', 'value': 'Eólica'},
            {'label': 'Hidráulica', 'value': 'Hidráulica'}
        ],
        value=['Nuclear', 'Solar fotovoltaica'],
        multi=True
    ),
    dcc.Graph(id='generation-graph')
])

# Callback para actualizar el gráfico
@app.callback(
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

if __name__ == '__main__':
    app.run_server(debug=True)
