import dash
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# External stylesheets
external_stylesheets = [dbc.themes.LITERA]

# Importar las páginas aquí

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, use_pages=True)
server = app.server

# Define your navbar
navbar = dbc.NavbarSimple(
    brand="Precio Luz Dashboard",
    brand_href="/",
    children=[
        dbc.NavItem(dbc.NavLink('Precios Hoy', href='/prices', active='exact')),
        dbc.NavItem(dbc.NavLink('Predicciones', href='/predictions', active='exact')),
        dbc.NavItem(dbc.NavLink('Análisis de Componentes', href='/components', active='exact')),
    ],
    sticky="top",
    color="dark",
    dark=True,
    className="mb-4"
)


app.layout = dbc.Container([
    dcc.Location(id='url', refresh=True),
    navbar,
    html.Div(
        dash.page_container,
        style={'margin': '50px'}  
    )], fluid=True)

@app.callback(
    Output('url', 'pathname'),
    [Input('url', 'pathname')]
)
def redirect_to_default(url):
    if url == '/':
        return '/prices'  # Redirige a la página de 'prices'
    return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=False)
