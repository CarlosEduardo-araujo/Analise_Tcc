import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import branca.colormap
import json

st.set_page_config(page_title="Alunos Eng. telecom IFCE", page_icon="", layout="wide")

# Função para converter colunas para snake_case
def snake_case(s):
    return s.strip().lower().replace(" ", "_").replace("-", "_")

# Carregar os dados do novo diretório e encoding
df = pd.read_csv(r"Data/matriculasFinal-phase2.csv", sep=';', encoding='latin')

# Converter todas as colunas para snake_case
df.columns = [snake_case(col) for col in df.columns]

# Corrigir a coluna cidade extraindo o nome da cidade
df["cidade"] = df["texto_cidade"].apply(lambda x: x[:-5] if isinstance(x, str) and len(x) > 5 else x)

# Criando coluna para saber se o aluno continua cursando ou não
df["status"] = df["desc_sit_matricula"].apply(lambda x: 'cursando' if x == 'Matriculado' else 'Formado' if x == 'Formado' else 'Não cursando')

# Criando coluna para saber a data do ultimo evento de matrícula
df["dt_ultimo_evento"] = df["ultimo_evento_matricula"].apply(lambda x: x.split(":")[1] if isinstance(x, str) else x)

df["ultimo_evento_matricula"] = df["ultimo_evento_matricula"].apply(lambda x: x.split(":")[0] if isinstance(x, str) else x)

df['dt_ultimo_evento'] = pd.to_datetime(df['dt_ultimo_evento'], errors='coerce')
df['dt_matricula'] = pd.to_datetime(df['dt_matricula'], errors='coerce')

df["tempo_permanencia"] = (df["dt_ultimo_evento"] - df["dt_matricula"]).dt.days / 365.25

df['tempo_permanencia_meses'] = (df['dt_ultimo_evento'] - df['dt_matricula']).dt.days / 30.44


# Preparar dados para o mapa
df_mapa = df.value_counts("cidade").reset_index(name="frequencia")
df_mapa["representatividade"] = (
    (df_mapa["frequencia"] / df_mapa["frequencia"].sum()) * 100
).round(2).astype(str) + "%"

# Carregar o geojson local com encoding UTF-8
geojson_url = r"geojson\geojs-23-mun.json"
with open(geojson_url, encoding="utf-8") as f:
    geojson_data = json.load(f)

st.title("Análise de Matrículas - Ensino Superior")

perguntas = [
    "1). Perfil dos alunos",
    "2). Situação acadêmica atual dos alunos",
    "3). Tempo médio de permanência no curso por perfil",
    "4). Relação entre tipo de escola de origem e rendimento acadêmico",
    "5). Relação entre situação de matricula e rendimento acadêmico"
]
escolha = st.sidebar.radio("Escolha uma pergunta:", perguntas)

def bar_with_percent(counts, x_label, y_label, title):
    percent = (counts / counts.sum() * 100).round(2)
    labels = [f"{v} ({p}%)" for v, p in zip(counts.values, percent.values)]
    fig = px.bar(
        x=counts.index, y=counts.values, text=labels,
        labels={'x': x_label, 'y': y_label}, title=title
    )
    fig.update_traces(textposition='outside')
    return fig

def grouped_bar_with_percent(df_grouped, x, y, color, x_label, y_label, title):
    # Calcula percentuais por grupo (x)
    total_por_x = df_grouped.groupby(x)[y].transform('sum')
    df_grouped['percent'] = (df_grouped[y] / total_por_x * 100).round(2)
    df_grouped['label'] = df_grouped.apply(lambda row: f"{row[y]} ({row['percent']}%)", axis=1)
    fig = px.bar(
        df_grouped, x=x, y=y, color=color, barmode='group',
        text='label', labels={x: x_label, y: y_label}, title=title
    )
    fig.update_traces(textposition='outside')
    return fig

if escolha == perguntas[0]:
    st.header("1. Perfil dos alunos")
    # Mapa inicial
    mapa_ceara = folium.Map(
        [-5.2637315250639025, -39.576651414308046],
        tiles="cartodbpositron",
        zoom_start=6.5
    )

    # Camada de fundo (opcional)
    folium.TileLayer(
        tiles=branca.utilities.image_to_url([[1,1], [1,1]]),
        attr="Carlos Bezerra", name="Imagem Fundo"
    ).add_to(mapa_ceara)

    # Mapa coroplético
    folium.Choropleth(
        geo_data=geojson_data,
        data=df_mapa,
        columns=["cidade", "frequencia"],
        key_on="feature.properties.name",
        fill_color="Reds",
        fill_opacity=0.9,
        line_opacity=0.5,
        legend_name="Alunos",
        nan_fill_color="white",
        name="Dados"
    ).add_to(mapa_ceara)

    # Destaque
    estilo = lambda x: {"fillColor": "white", "color": "black", "fillOpacity": 0.001, "weight": 0.001}
    estilo_destaque = lambda x: {"fillColor": "darkblue", "color": "black", "fillOpacity": 0.5, "weight": 1}
    highlight = folium.features.GeoJson(
        data=geojson_data,
        style_function=estilo,
        highlight_function=estilo_destaque,
        name="Destaque"
    )
    folium.features.GeoJsonTooltip(
        fields=["name",],
        aliases=["cidade"],
        labels=False,
        style=("background-color: white; color: black; font-family: arial; font-size: 16px; padding: 10px;")
    ).add_to(highlight)
    mapa_ceara.add_child(highlight)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Mapa Interativo")
        st_folium(mapa_ceara, width=700, height=500)
    with col2:
        st.subheader("Quantidade de egressos")
        st.dataframe(df_mapa, height=500)

    st.subheader("Idade média dos alunos")
    df['dt_nascimento'] = pd.to_datetime(df['dt_nascimento'], errors='coerce')
    df['idade'] = (pd.Timestamp('today') - df['dt_nascimento']).dt.days // 365
    st.write(f"Idade média: {df['idade'].mean():.1f} anos")
    # Histograma de idade com representatividade
    idade_counts = df['idade'].value_counts().sort_index()
    idade_percent = (idade_counts / idade_counts.sum() * 100).round(2)
    idade_labels = [f"{v} ({p}%)" for v, p in zip(idade_counts.values, idade_percent.values)]
    fig = px.bar(
        x=idade_counts.index, y=idade_counts.values, text=idade_labels,
        labels={'x': 'Idade', 'y': 'Quantidade'}, title="Distribuição de Idade"
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig)

    st.subheader("Distribuição por sexo")
    sexo_counts = df['sexo'].value_counts()
    st.plotly_chart(bar_with_percent(sexo_counts, 'Sexo', 'Quantidade', "Sexo"))

    st.subheader("Distribuição por cor/raça")
    cor_counts = df['desc_cor'].value_counts()
    st.plotly_chart(bar_with_percent(cor_counts, 'Cor/Raça', 'Quantidade', "Cor/Raça"))

    st.subheader("Tipo de escola de origem")
    escola_counts = df['desc_tipo_escola_origem'].value_counts()
    st.plotly_chart(bar_with_percent(escola_counts, 'Tipo de Escola', 'Quantidade', "Tipo de Escola de Origem"))



elif escolha == perguntas[1]:
    st.header("2. Situação acadêmica atual dos alunos")

    st.subheader("Situação da matrícula")
    sit_counts = df['desc_sit_matricula'].value_counts()
    st.plotly_chart(bar_with_percent(sit_counts, 'Situação', 'Quantidade', "Situação da Matrícula"))

    st.subheader("Abandono por letivo inicial")
    ult_per_counts = df[df['desc_sit_matricula'] == "Abandono"]['ano_letivo_ini'].value_counts()
    st.plotly_chart(bar_with_percent(ult_per_counts, 'Ano letivo', 'Quantidade', "Abandono por Período Letivo Inicial"))

    st.subheader("Cursando por ano letivo inicial")
    per_counts = df[df['desc_sit_matricula'] == "Matriculado"]['ano_letivo_ini'].value_counts()
    st.plotly_chart(bar_with_percent(per_counts, 'Situação no Período', 'Quantidade', "Cursando por ano letivo inicial"))


elif escolha == perguntas[2]:
    st.header("3. Tempo médio de permanência no curso por perfil")

    st.subheader("Tempo médio de permanência (em anos)")
    st.write(f"Tempo médio: {df['tempo_permanencia'].mean():.1f} anos")

    st.subheader("Tempo de permanência por sexo")
    fig = px.box(
        df, x='sexo', y='tempo_permanencia', color='sexo',
        points="all", title="Tempo de Permanência por Sexo"
    )
    st.plotly_chart(fig)

    st.subheader("Tempo de permanência por tipo de escola de origem")
    fig = px.box(
        df, x='desc_tipo_escola_origem', y='tempo_permanencia', color='desc_tipo_escola_origem',
        points="all", title="Tempo de Permanência por Tipo de Escola de Origem"
    )
    st.plotly_chart(fig)

    st.subheader("Tempo de permanência por situação da matrícula")
    fig = px.box(
        df, x='status', y='tempo_permanencia', color='status',
        points="all", title="Tempo de Permanência por Situação da Matrícula"
    )
    st.plotly_chart(fig)

elif escolha == perguntas[3]:
    st.header("4. Relação entre tipo de escola de origem e rendimento acadêmico")

    st.subheader("Coeficiente de rendimento por tipo de escola de origem")
    fig = px.box(
        df, x='desc_tipo_escola_origem', y='coeficiente_rendimento', color='desc_tipo_escola_origem',
        points="all", title="Coeficiente de Rendimento por Tipo de Escola de Origem"
    )
    st.plotly_chart(fig)

   # st.write(df.groupby('desc_tipo_escola_origem')['coeficiente_rendimento'].describe())


elif escolha == perguntas[4]:
    st.header("5. Relação entre situação de matricula e rendimento acadêmico")

    st.write("teste")

    st.subheader("Coeficiente de rendimento por situação de matricula.")
    fig = px.box(
        df, x='desc_sit_matricula', y='coeficiente_rendimento', color='desc_sit_matricula',
        points="all", title="Coeficiente de Rendimento por Tipo de Escola de Origem"
    )
    st.plotly_chart(fig)

   # st.write(df.groupby('desc_sit_matricula')['coeficiente_rendimento'].describe())