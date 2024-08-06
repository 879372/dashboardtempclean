import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import datetime
import locale
from flask import Flask
from waitress import serve
from dash_bootstrap_templates import ThemeSwitchAIO
from dash.exceptions import PreventUpdate
import threading
import fdb
import hashlib
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Dashboard Temp Clean'

tab_card = {'height': '100%'}

main_config = {
    "hovermode": "x unified",
    "legend": {"yanchor":"top",
                "y":0.9,
                "xanchor":"left",
                "x":0.1,
                "title": {"text": None},
                "font" :{"color":"white"},
                "bgcolor": "rgba(0,0,0,0.5)"},
    "margin": {"l":10, "r":10, "t":10, "b":10}
}

config_graph={"displayModeBar": False, "showTips": False}

template_theme1 = "flatly"
template_theme2 = "darkly"
url_theme1 = dbc.themes.FLATLY
url_theme2 = dbc.themes.DARKLY
lock = threading.Lock()     
                     
def obter_dados_firebird():
        conn = fdb.connect(
            host='localhost', database='C:/TNC/Dados/DADOS.FDB',
            user='SYSDBA', password='masterkey',
            charset='ANSI'
        )

        query = """
            SELECT                                                                  
                EXTRACT(DAY FROM VM.data_emissao) AS DIA,
                EXTRACT(MONTH FROM VM.DATA_EMISSAO) AS MES,
                EXTRACT(YEAR FROM VM.DATA_EMISSAO) AS ANO,
                E.FANTASIA AS EMPRESA,
                V.NOME AS VENDEDOR,
                P.MUNICIPIO,
                P.UF,
                VM.TOTAL AS VALOR_PAGO,
                VM.cfop
            FROM nfe_master VM
            INNER JOIN EMPRESA E ON VM.FKEMPRESA = E.CODIGO
            LEFT JOIN PESSOA P ON VM.ID_CLIENTE = P.CODIGO
            LEFT JOIN VENDEDORES V ON p.fk_vendedor = V.CODIGO
            WHERE VM.SITUACAO = 2
        """

        df = pd.read_sql(query, conn)
        df_cru = df.copy()
        conn.close()
        return df

df = obter_dados_firebird()
df_cru = df

def convert_to_text(month):
    match month:
        case 0:
            x = 'Mês atual'
        case 1:
            x = 'Jan'
        case 2:
            x = 'Fev'
        case 3:
            x = 'Mar'
        case 4:
            x = 'Abr'
        case 5:
            x = 'Mai'
        case 6:
            x = 'Jun'
        case 7:
            x = 'Jul'
        case 8:
            x = 'Ago'
        case 9:
            x = 'Set'
        case 10:
            x = 'Out'
        case 11:
            x = 'Nov'
        case 12:
            x = 'Dez'
    return x

def convert_text(month):
    match month:
        case 0:
            x = 'Mês atual'
        case 1:
            x = 'Janeiro'
        case 2:
            x = 'Fevereiro'
        case 3:
            x = 'Março'
        case 4:
            x = 'Abril'
        case 5:
            x = 'Maio'
        case 6:
            x = 'Junho'
        case 7:
            x = 'Julho'
        case 8:
            x = 'Agosto'
        case 9:
            x = 'Setembro'
        case 10:
            x = 'Outubro'
        case 11:
            x = 'Novembro'
        case 12:
            x = 'Dezembro'
    return x

mes_atual = datetime.datetime.now().month
ano_atual = datetime.datetime.now().year
locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')

def formatar_reais(valor):
    return locale.currency(valor, grouping=True)

def year_filter(year):
    if year == 0:
        mask = df['ANO'].isin([datetime.datetime.now().year])
    else:
       mask = df['ANO'].isin([year])
    return mask

def month_filter(month):
    if month == 0:
        mask = df['MES'].isin([datetime.datetime.now().month])
    else:
       mask = df['MES'].isin([month])
    return mask

def year_month_filter(year, month):
    if year == 0 and month == 0:
        mask = df['ANO'].isin([datetime.datetime.now().year]) & df['MES'].isin([datetime.datetime.now().month])
    elif year == 0:
        mask = df['MES'].isin([month])
    elif month == 0:
        mask = df['ANO'].isin([year])
    else:
        mask = (df['ANO'] == year) & (df['MES'] == month)
    return mask

def team_filter(team):
     if team == 0:
         mask = df['EMPRESA'].isin(df['EMPRESA'].unique())
     else:
         mask = df['EMPRESA'].isin([team])
     return mask

authenticated = False
center_style = {'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'height': '100vh'}
login_layout = html.Div(
    [
        html.Div(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Img(src=r'assets/logotemp.png', alt='logo',className='logo input1'),
                        html.Br(),
                        dbc.Input(id='username', type='text', placeholder='Usuário', className='input'),
                        html.Br(),
                        dbc.Input(id='password', type='password', placeholder='Senha', className='input'),
                        html.Br(),
                        dbc.Button("Entrar", id='login-button', style={'background-color': 'blue', 'border': 'none'}, className='logo input'),  
                        html.Div(id='login-output')
                    ]
                )
            ), style={'max-width': '400px'}
        )
    ], style=center_style
)

main_layout = dbc.Container(children=[
    dbc.Row([    html.Link(
        rel='shortcut icon',
        href='/assets/favicon.ico'
    ),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Legend("TEMP CLEAN")
                        ], sm=8),
                        dbc.Col([
                            html.I(className='logo', style={'font-size': '300%'})
                        ], sm=4, align="center")
                    ]),
                    dbc.Row([
                        dbc.Col([
                            ThemeSwitchAIO(aio_id="theme", themes=[url_theme1, url_theme2]),
                            html.Legend("Dashboard de Vendas")
                        ])
                    ], style={'margin-top': '10px'}),
                    dbc.Row([
                    html.Div(
                        className='logo-container',
                        children=[
                            html.Img(src=r'assets/logotemp.png', alt='logo',className='logo')
                        ]),
                        html.Div(
                            className='button-container',
                            children=[
                                dbc.Button("Sair", id='logout-button', style={'background-color': 'blue', 'border': 'none', 'margin-top':'15px'}, className='logo input'),
                                html.Div(id='logout-output')
                            ]),
                    ], style={'margin-top': '10px'})
                ])
            ], style=tab_card)
        ], sm=4, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(
                        dbc.Col(
                            html.Legend('Top Vendedores')
                        )
                    ),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='graph1', className='dbc', config=config_graph)
                        ], sm=12, md=7),
                        dbc.Col([
                            dcc.Graph(id='graph2', className='dbc', config=config_graph)
                        ], sm=12, lg=5)
                    ])
                ])
            ], style=tab_card)
        ], sm=12, lg=7),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(
                        dbc.Col([
                            html.H5('Escolha o ANO'),
                            dbc.RadioItems(
                                id="radio-year",
                                options=[],
                                value=ano_atual if ano_atual in df['ANO'].unique() else 0,
                                inline=True,
                                labelCheckedClassName="text-success",
                                inputCheckedClassName="border border-success bg-success",
                            ),
                            html.Div(id='year-selecty', style={'text-align': 'center', 'margin-top': '30px'}, className='dbc'),
                            html.H5('Escolha o MÊS'),
                            dbc.RadioItems(
                                id="radio-month",
                                options=[],
                                value=mes_atual if mes_atual in df['MES'].unique() else 0,
                                inline=True,
                                labelCheckedClassName="text-success",
                                inputCheckedClassName="border border-success bg-success",
                            ),
                            html.Div(id='month-select', style={'text-align': 'center', 'margin-top': '30px'}, className='dbc')
                        ])
                    )
                ])
            ], style=tab_card)
        ], sm=12, lg=3)
    ], className='g-2 my-auto', style={'margin-top': '7px'}),

    # Row 2
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='graph3', className='dbc', config=config_graph)
                        ])
                    ], style=tab_card)
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='graph4', className='dbc', config=config_graph)
                        ])
                    ], style=tab_card)
                ])
            ], className='g-2 my-auto', style={'margin-top': '7px'})
        ], sm=12, lg=5),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='graph5', className='dbc', config=config_graph)
                        ])
                    ], style=tab_card)
                ], sm=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='graph6', className='dbc', config=config_graph)
                        ])
                    ], style=tab_card)
                ], sm=6)
            ], className='g-2'),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dcc.Graph(id='graph7', className='dbc', config=config_graph)
                    ], style=tab_card)
                ])
            ], className='g-2 my-auto', style={'margin-top': '7px'})
        ], sm=12, lg=4),
        dbc.Col([
            dbc.Card([
                dcc.Graph(id='graph8', className='dbc', config=config_graph)
            ], style=tab_card)
        ], sm=12, lg=3)
    ], className='g-2 my-auto', style={'margin-top': '7px'}),

    # Row 3
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('Distribuição de Faturamento por Empresa'),
                    dcc.Graph(id='graph9', className='dbc', config=config_graph)
                ])
            ], style=tab_card)
        ], sm=12, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Faturamento Mensal por Empresa"),
                    dcc.Graph(id='graph10', className='dbc', config=config_graph)
                ])
            ], style=tab_card)
        ], sm=12, lg=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='graph12', className='dbc', config=config_graph)
                ])
            ], style=tab_card)
        ], sm=12, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='graph11', className='dbc', config=config_graph)
                ])
            ], style=tab_card)
        ], sm=12, lg=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5('Escolha a EMPRESA'),
                    dbc.RadioItems(
                        id="radio-team",
                        options=[],
                        value=0,
                        inline=True,
                        labelCheckedClassName="text-warning",
                        inputCheckedClassName="border border-warning bg-warning",
                    ),
                    html.Div(id='team-select', style={'text-align': 'center', 'margin-top': '30px'}, className='dbc'),
                ]),    html.Div(id="output-dados"),
            ], style=tab_card)
        ], sm=12, lg=2),
    ], className='g-2 my-auto', style={'margin-top': '7px'}),
        dcc.Interval(
        id='interval-component',
        interval=5 * 60 * 1000,  
        n_intervals=0
    )
], fluid=True, style={'height': '100vh'})

@app.callback(
    Output("output-dados", "children"),
    Input('interval-component', 'n_intervals')
)
def recarregar_dados(n_intervals):
    global df
    with lock:
        try:
            df = obter_dados_firebird()
        except Exception as e:
            print(f"Erro ao obter dados do Firebird: {e}")
    return None

df = obter_dados_firebird()

@app.callback(
    Output('graph1', 'figure'),
    Output('graph2', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph1e2( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_month = month_filter(month)
            mask_team = team_filter(team)
            df_filtered = df.loc[mask_year & mask_month & mask_team]


            # Grafico 1
            df_1 = df_filtered.groupby(['EMPRESA', 'VENDEDOR'])['VALOR_PAGO'].sum().reset_index()
            df_1 = df_1.groupby('VENDEDOR').head(1).reset_index()
            df_1 = df_1.sort_values(by='VALOR_PAGO', ascending=False)
            df_1 = df_1.head(4)
            df_1['TOTAL_VENDAS'] = df_1['VALOR_PAGO'].map(formatar_reais)
            fig1 = go.Figure(go.Bar(x=df_1['VENDEDOR'], y=df_1['VALOR_PAGO'], textposition='auto', text=df_1['TOTAL_VENDAS']))
            fig1.update_layout(main_config, height=200, template=template)

            # Grafico 2
            fig2 = go.Figure(go.Pie(labels=df_1['VENDEDOR'] + ' - ' + df_1['EMPRESA'], values=df_1['VALOR_PAGO'], hole=.6))
            fig2.update_layout(main_config, height=200, template=template, showlegend=False)
        except Exception as e:
            print(f"Erro ao obter dados do graph 1 e 2: {e}")
        return fig1, fig2


@app.callback(
    Output('graph3', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph3( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_month = month_filter(month)
            mask_team = team_filter(team)
            df_filtered = df.loc[mask_year & mask_month & mask_team]

            #Grafico 3
            df_3 = df_filtered.groupby('DIA')['VALOR_PAGO'].sum().reset_index()
            df_3['TOTAL_VENDAS'] = df_3['VALOR_PAGO'].map(formatar_reais)
            fig3 = go.Figure(go.Scatter(x=df_3['DIA'], y=df_3['VALOR_PAGO'], fill='tonexty', text=df_3['TOTAL_VENDAS'], hoverinfo='text'))
            fig3.add_annotation(text='Faturamento por dia do Mês',xref="paper", yref="paper", font=dict( size=17, color='gray'), align="center", bgcolor="rgba(0,0,0,0.8)", x=0.05, y=0.85, showarrow=False)
            fig3.update_layout(main_config, height=180, template=template)
        except Exception as e:
            print(f"Erro ao obter dados do graph 3: {e}")
        return fig3

@app.callback(
    Output('graph4', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph4( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_team = team_filter(team)
            mask_zero = year_month_filter(year, 0)
            df_team_zero = df.loc[mask_zero & mask_team]

            #Grafico 4
            df_4 = df_team_zero.groupby('MES')['VALOR_PAGO'].sum().reset_index()
            df_4['TOTAL_VENDAS'] = df_4['VALOR_PAGO'].map(formatar_reais)
            fig4 = go.Figure(go.Scatter(x=df_4['MES'], y=df_4['VALOR_PAGO'], fill='tonexty', text=df_4['TOTAL_VENDAS'], hoverinfo='text'))
            fig4.add_annotation(text='Faturamento por Mês', xref="paper", yref="paper",font=dict( size=20, color='gray'),align="center", bgcolor="rgba(0,0,0,0.8)",x=0.05, y=0.85, showarrow=False)
            fig4.update_layout(main_config, height=180, template=template)
        except Exception as e:
            print(f"Erro ao obter dados do graph 4: {e}")
        return fig4
 
 
@app.callback(
    Output('graph5', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph5( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_month = month_filter(month)
            mask_team = team_filter(team)
            df_filtered = df.loc[mask_year & mask_month & mask_team]

            #Grafico 5
            df_5 = df_filtered.groupby(['VENDEDOR', 'EMPRESA'])['VALOR_PAGO'].sum()
            df_5.sort_values(ascending=False, inplace=True)
            df_5 = df_5.reset_index()
            fig5 = go.Figure()
            if not df_5.empty:
                fig5.add_trace(go.Indicator(mode='number+delta',
                            title={"text": f"<span>{df_5['VENDEDOR'].iloc[0]}</span><br><span style='font-size:70%'>Em vendas - em relação à média</span><br>"},
                            value=df_5['VALOR_PAGO'].iloc[0],
                            number={'prefix': "R$"},
                            delta={'relative': True, 'valueformat': '.1%', 'reference': df_5['VALOR_PAGO'].mean()}
                ))
            else:
                fig5.add_trace(go.Indicator(mode='number+delta', value=0, number={'prefix': "R$"}, title={"text": f"<span>- Top Vendador</span>"}))
            fig5.update_layout(main_config, height=200, template=template)
            fig5.update_layout({"margin": {"l": 0, "r": 0, "t": 50, "b": 0}})
        except Exception as e:
            print(f"Erro ao obter dados do graph 5: {e}")
        return fig5


@app.callback(
    Output('graph6', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph6( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_month = month_filter(month)
            mask_team = team_filter(team)
            df_filtered = df.loc[mask_year & mask_month & mask_team]

            #Grafico 6
            df_6 = df_filtered.groupby('EMPRESA')['VALOR_PAGO'].sum()
            df_6.sort_values(ascending=False, inplace=True)
            df_6 = df_6.reset_index()
            fig6 = go.Figure()
            if not df_6.empty:
                fig6.add_trace(go.Indicator(mode='number+delta',
                            title={"text": f"<span>{df_6['EMPRESA'].iloc[0]}</span><br><span style='font-size:70%'>Em vendas - em relação à média</span><br>"},
                            value=df_6['VALOR_PAGO'].iloc[0],
                            number={'prefix': "R$"},
                            delta={'relative': True, 'valueformat': '.1%', 'reference': df_6['VALOR_PAGO'].mean()}
                ))
            else:
                fig6.add_trace(go.Indicator(mode='number+delta', value=0, number={'prefix': "R$"}, title={"text": f"<span>- Top Empresa</span>"}))
            fig6.update_layout(main_config, height=200, template=template)
            fig6.update_layout({"margin": {"l": 0, "r": 0, "t": 50, "b": 0}})
        except Exception as e:
            print(f"Erro ao obter dados do graph 6: {e}")
        return fig6


@app.callback(
    Output('graph7', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph7( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_zero = year_month_filter(year, 0)
            df_zero = df.loc[mask_zero]


            #Grafico 7
            df_7_group = df_zero.groupby(['MES', 'EMPRESA'])['VALOR_PAGO'].sum().reset_index()
            df_7_total = df_zero.groupby('MES')['VALOR_PAGO'].sum().reset_index()
            fig7 = px.line(df_7_group, y="VALOR_PAGO", x="MES", color="EMPRESA")
            fig7.add_trace(go.Scatter(y=df_7_total["VALOR_PAGO"], x=df_7_total["MES"], mode='lines+markers', fill='tonexty', name='Total de Vendas'))
            fig7.update_layout(main_config, yaxis={'title': None}, xaxis={'title': None}, height=190, template=template)
            fig7.update_layout({"legend": {"yanchor": "top", "y": 0.99, "font": {"color": "white", 'size': 10}}})
        except Exception as e:
            print(f"Erro ao obter dados do graph 7: {e}")
        return fig7


@app.callback(
    Output('graph8', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph8( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_month = month_filter(month)
            mask_team = team_filter(team)
            df_filtered = df.loc[mask_year & mask_month & mask_team]

            df_8 = df_filtered.groupby('EMPRESA')['VALOR_PAGO'].sum().reset_index()
            df_8['TOTAL_VENDAS'] = df_8['VALOR_PAGO'].map(formatar_reais)
            fig8 = go.Figure(go.Bar( x=df_8['EMPRESA'], y=df_8['VALOR_PAGO'], orientation='v', textposition='auto', text=df_8['TOTAL_VENDAS'], hoverinfo='text',insidetextfont=dict(family='Times', size=12)))
            fig8.update_layout(main_config, height=360, template=template)
        except Exception as e:
            print(f"Erro ao obter dados do graph 8: {e}")
        return fig8


@app.callback(
    Output('graph9', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph9( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_month = month_filter(month)
            df_meseano = df.loc[mask_year & mask_month]
            
            #Grafico 9
            df_9 = df_meseano.groupby('EMPRESA')['VALOR_PAGO'].sum().reset_index()
            fig9 = go.Figure()
            fig9.add_trace(go.Pie(labels=df_9['EMPRESA'], values=df_9['VALOR_PAGO'], hole=.7))
            fig9.update_layout(main_config, height=150, template=template, showlegend=False)
        except Exception as e:
            print(f"Erro ao obter dados do graph 9: {e}")
        return fig9


@app.callback(
    Output('graph10', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph10( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_team = team_filter(team)
            mask_zero = year_month_filter(year, 0)
            df_team_zero = df.loc[mask_zero & mask_team]
            
            #Grafico 10
            df10 = df_team_zero.groupby(['EMPRESA', 'MES'])['VALOR_PAGO'].sum().reset_index()
            df10['TOTAL_VENDAS'] = df10['VALOR_PAGO'].map(formatar_reais)
            fig10 = px.line(df10, y="TOTAL_VENDAS", x="MES", color="EMPRESA")
            fig10.update_layout(main_config, height=200, template=template, showlegend=False)
        except Exception as e:
            print(f"Erro ao obter dados do graph 10: {e}")
        return fig10

@app.callback(
    Output('graph11', 'figure'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph11( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_month = month_filter(month)
            mask_team = team_filter(team)
            df_filtered = df.loc[mask_year & mask_month & mask_team]
            
            #Grafico 11
            df_11 = df_filtered
            fig11 = go.Figure()
            if not df_11.empty:
                fig11.add_trace(go.Indicator(mode='number',
                            title={"text": f"<span style='font-size:150%'>Vendas do Mês</span><br><span style='font-size:70%'>Em Reais</span><br>"},
                            value=df_11['VALOR_PAGO'].sum(),
                            number={'prefix': "R$"}
                ))
            else:
                fig11.add_trace(go.Indicator(mode='number', value=0, number={'prefix': "R$"}, title={"text": f"<span>Vendas Mensal</span>"}))
            fig11.update_layout(main_config, height=300, template=template)

        except Exception as e:
            print(f"Erro ao obter dados do graph 11: {e}")
        return fig11

@app.callback(
    Output('graph12', 'figure'),
    Output('month-select', 'children'),
    Input('radio-month', 'value'),
    Input('radio-year', 'value'),
    Input('radio-team', 'value'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input('interval-component', 'n_intervals')  
)
def update_graph12( month, year, team, toggle, n_intervals):
    with lock:
        try:
            template = template_theme1 if toggle else template_theme2
            global df

            mask_year = year_filter(year)
            mask_month = month_filter(month)
            mask_team = team_filter(team)
            df_filtered = df.loc[mask_year & mask_month & mask_team]

            #Grafico 12
            today = datetime.datetime.now()
            df_12 = df_filtered[(df_filtered['DIA'] == today.day) & (df_filtered['MES'] == today.month) & (df_filtered['ANO'] == today.year)].groupby('EMPRESA')['VALOR_PAGO'].sum()
            df_12.sort_values(ascending=False, inplace=True)
            df_12 = df_12.reset_index()
            fig12 = go.Figure()

            if not df_12.empty:
                fig12.add_trace(go.Indicator(
                            title={"text": f"<span style='font-size:150%'>Vendas de Hoje</span><br><span style='font-size:70%'>Em Reais</span><br>"},
                            value=df_12['VALOR_PAGO'].sum(),
                            number={'prefix': "R$"}
                ))
            else:
                fig12.add_trace(go.Indicator(
                    mode='number',
                    value=0,
                    number={'prefix': "R$"},
                    title={"text": f"<span>Vendas diária</span>"}
                ))

            fig12.update_layout(main_config, height=300, template=template)


            select = html.H1("Todas as EMPRESAS") if team == 0 else html.H1(team)
            select = html.H1(convert_text(month))
        except Exception as e:
            print(f"Erro ao obter dados do graph 12: {e}")
    return  fig12, select

@app.callback(
    Output("radio-year", "options"),
    Output("radio-year", "value"),
    Output("radio-month", "options"),
    Output("radio-month", "value"),
    Output("radio-team", "options"),
    Output("radio-team", "value"),
    Input('interval-component', 'n_intervals'),
    Input('radio-year', 'value')
)
def update_radio_buttons(n_intervals, selected_year):
    with lock:
        try:
            mes_atual = datetime.datetime.now().month
            ano_atual = datetime.datetime.now().year
            unique_years = sorted(df['ANO'].unique(), reverse=True)
            options_year = [{'label': i, 'value': i} for i in unique_years]

            selected_year = selected_year or ano_atual

            if selected_year:
                df_filtered = df[df['ANO'] == selected_year]
                options_month = [{'label': convert_to_text(i), 'value': j} for i, j in zip(df_filtered['MES'].unique(), df_filtered['MES'].unique())]
                options_month = sorted(options_month, key=lambda x: x['value'])

                if selected_year == ano_atual:
                    default_month = mes_atual
                else:
                    default_month = options_month[0]['value']


            else:
                options_month = []
                default_month = options_month[0]['value']

            options_team = [{'label': 'Todas as Empresas', 'value': 0}]
            for i in df['EMPRESA'].unique():
                options_team.append({'label': i, 'value': i})
        except Exception as e:
            print(f"Erro ao obter dados do Firebird: {e}")

    return options_year, selected_year, options_month, default_month, options_team, 0

@app.callback(
    Output('login-output', 'children'),
    [Input('login-button', 'n_clicks')],
    [State('username', 'value'),
     State('password', 'value')]
)
def check_login(n_clicks, username, password):
    global authenticated
    
    if n_clicks is not None:
        conexao = fdb.connect(
            host='localhost', database='C:/TNC/Dados/DADOS.FDB',
            user='SYSDBA', password='masterkey',
            charset='ANSI'
        )

        cursor = conexao.cursor()
        sql = """
        SELECT login, senha_dash
        FROM usuarios
        WHERE login = ? AND senha_dash = ?
        """
        cursor.execute(sql, (username.upper().strip(), hashlib.md5(password.encode()).hexdigest()))
        result = cursor.fetchone()
        cursor.close()
        print(password)
        print(hashlib.md5(password.encode()).hexdigest())
        if result:  # Se a consulta retornar algo
            authenticated = True
            return dcc.Location(pathname='/home', id='main_layout_redirect')
        else:
            authenticated = False
            return html.Div('Credenciais inválidas. Tente novamente.', style={'color': 'red'})


@app.callback(
    Output('url', 'pathname'),
    [Input('main_layout_redirect', 'pathname')]
)
def update_url(pathname):
    if pathname is not None:
        return pathname

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    global authenticated 
    if pathname == '/home' and authenticated:  
        return main_layout
    elif not authenticated:  
        return login_layout  
    else:
        return login_layout 
         
@app.callback(
    Output('logout-output', 'children'),
    [Input('logout-button', 'n_clicks')],
    [State('url', 'pathname')]
)
def update_output(n_clicks, pathname):
    if n_clicks is None:
        raise PreventUpdate
    return dcc.Location(pathname='/', id='main_layout_redirect')

mode = 'prod'

if __name__ == '__main__':
    if mode == 'dev':
        app.run(host='0.0.0.0', port='8050')
    else:
        serve(app.server, host='0.0.0.0', port='8050', threads=20)

