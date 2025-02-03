import streamlit as st
import pandas as pd
import folium 
import branca.colormap
from streamlit_folium import st_folium
import inflection
from functions import snake_case
import plotly.graph_objects as go

st.set_page_config(page_title="Alunos Eng. telecom IFCE", page_icon="", layout="wide")

geojson_url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-23-mun.json"

#lendo o arquivo 
df_raw = pd.read_csv(r"Data\matriculasFinal-phase2.csv",sep=';', encoding='latin')
snake_case(df_raw)

df_raw["cidade"] = df_raw["texto_cidade"].apply(lambda x: x if pd.isna(x) else x[:-5])
#df_raw["cidade"] = df_raw["texto_cidade"].apply(lambda x: x if pd.isna(x) else x.split(' ')[0])

df_mapa = df_raw.value_counts("cidade")

st.title("Análise dos egressos Engenharia de telecomunicações IFCE.")

st.dataframe(df_raw.head()) 

st.subheader("perguntas a serem respondidas:")
st.subheader("1 Qual a distribuição dos alunos por cidade ?")

#Mapa inicial   
mapa_ceara = folium.Map([-5.2637315250639025, -39.576651414308046], 
                         tiles = "cartodbpositron",
                         zoom_start = 6.5)

folium.TileLayer(tiles = branca.utilities.image_to_url([[1,1], [1,1]]),
                attr = "Carlos Bezerra", name = "Imagem Fundo").add_to(mapa_ceara)

#Criando o mapa coropletico
folium.Choropleth(geo_data = geojson_url,
                 data = df_mapa,
                 columns= ["cidade", "cod_matricula"],
                 key_on = "feature.properties.name",
                 fill_color = "OrRd",
                 fill_opacity = 0.9,
                 line_opacity = 0.5,
                 legend_name = "Alunos",
                 nan_fill_color = "white",
                 name = "Dados").add_to(mapa_ceara)


#Adicionando a função de destaque
estilo = lambda x: {"fillColor": "white",
                   "color": "black",
                   "fillOpacity": 0.001,
                   "weight": 0.001}

estilo_destaque = lambda x: {"fillColor": "darkblue",
                            "color": "black",
                            "fillOpacity": 0.5,
                            "weight": 1}

highlight = folium.features.GeoJson(data = geojson_url,
                                   style_function = estilo,
                                   highlight_function = estilo_destaque,
                                   name = "Destaque")

#Adicionando caixa de texto
folium.features.GeoJsonTooltip(fields = ["name",],
                               aliases = ["cidade"],
                               labels = False,
                               style = ("background-color: white; color: black; font-family: arial; font-size: 16px; padding: 10px;")).add_to(highlight)

#Adicionando o destaque ao mapa
mapa_ceara.add_child(highlight)


col1, col2 = st.columns([2, 1])

# Exibindo o mapa na primeira coluna
with col1:
    st.subheader("Mapa Interativo")
    st_folium(mapa_ceara, width=700, height=500)

# Exibindo o DataFrame na segunda coluna
with col2:
    st.subheader("Quantidade de egressos")
    st.dataframe(df_mapa, height=500)

st.subheader("2 Qual a quantidade de abandonos por ano letivo?")


datas = df_raw[df_raw["situacao_ultimo_periodo_letivo"] == "Abandonou"]
datas = pd.DataFrame(datas["ano_let_atual"].value_counts()).reset_index().sort_values("ano_let_atual")



# Curva
fig = go.Figure(go.Scatter(x = datas["ano_let_atual"],
                          y = datas["count"],
                          mode = "lines",
                          line_shape = "spline",
                          line = dict(color = "rgb(82,106,131)",
                                     width = 4)))

# Pontos
fig.add_trace(go.Scatter(x = datas["ano_let_atual"],
                        y = datas["count"],
                        mode = "markers+text",
                        text = datas["count"],
                        textposition = "top center",
                        marker = dict(color = "black",
                                     size = 6)))

#Títulos
fig.update_layout(title = "Distribuição de Abandonos por Ano Letivo",
                 xaxis_title = "Ano Letivo",
                 yaxis_title = "Quantidade")

#Plano de Fundo e Eixos
fig.update_layout(xaxis = dict(showline = False,
                              showgrid = False,     
                              showticklabels = True,
                              linecolor = "grey",
                              linewidth = 2,
                              ticks = "outside"),
                 yaxis = dict(linecolor = "grey",
                              linewidth = 2,
                              showgrid = False,
                              showline = False,
                              ticks = "outside"),
                 plot_bgcolor = "white",
                 showlegend = False)


st.plotly_chart(fig)







st.subheader("3 Qual o total de matriculas por sexo por ano ?")

#df_gen = df_raw[df_raw["sexo"] == "M"]
df_gen = pd.DataFrame(df_raw["sexo"].value_counts()).reset_index().sort_values("sexo")



# Curva
fig3 = go.Figure(go.Scatter(x = df_gen["sexo"],
                          y = df_gen["count"],
                          mode = "lines",
                          line_shape = "spline",
                          line = dict(color = "rgb(82,106,131)",
                                     width = 4)))

# Pontos
fig3.add_trace(go.Scatter(x = datas["sexo"],
                        y = datas["count"],
                        mode = "markers+text",
                        text = datas["count"],
                        textposition = "top center",
                        marker = dict(color = "black",
                                     size = 6)))

#Títulos
fig3.update_layout(title = "Distribuição de Abandonos por Ano Letivo",
                 xaxis_title = "Ano Letivo",
                 yaxis_title = "Quantidade")

#Plano de Fundo e Eixos
fig3.update_layout(xaxis = dict(showline = False,
                              showgrid = False,     
                              showticklabels = True,
                              linecolor = "grey",
                              linewidth = 2,
                              ticks = "outside"),
                 yaxis = dict(linecolor = "grey",
                              linewidth = 2,
                              showgrid = False,
                              showline = False,
                              ticks = "outside"),
                 plot_bgcolor = "white",
                 showlegend = False)


st.plotly_chart(fig3)

st.subheader("3 Como a situação de matrículas dos alunos estão distribuídas em relação ao sexo")

st.subheader("4 Qual é a distribuição das situações de matrícula (ativo, trancado, jubilado, etc.)?")


