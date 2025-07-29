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
df.columns = [snake_case(col) for col in df.columns]
df = df[df["ano_letivo_ini"] >= 2014]  # Filtrar anos a partir de 2014

# Corrigir a coluna cidade extraindo o nome da cidade
df["cidade"] = df["texto_cidade"].apply(lambda x: x[:-5] if isinstance(x, str) and len(x) > 5 else x)


# Criando coluna para saber se o aluno continua cursando ou não
df["status"] = df["desc_sit_matricula"].apply(
    lambda x: 'Matriculado' if x in ['Matriculado', 'Concludente', 'Estagiario (Concludente)']
    else 'Egresso' if x == 'Formado'
    else 'Sem êxito'
)

# Criando coluna para agrupar cor/raça
df["grupo"] = df["desc_cor"].apply(
    lambda x: 'PPI' if x in ['Preta', 'Parda', 'Indígena']
    else 'Branca e amarela' if x in['Branca', 'Amarela'] 
    else 'Sem informação'
)

# Criando coluna para saber a data do ultimo evento de matrícula
df["dt_ultimo_evento"] = df["ultimo_evento_matricula"].apply(lambda x: x.split(":")[1] if isinstance(x, str) else x)
df["ultimo_evento_matricula"] = df["ultimo_evento_matricula"].apply(lambda x: x.split(":")[0] if isinstance(x, str) else x)

df['dt_ultimo_evento'] = pd.to_datetime(df['dt_ultimo_evento'], dayfirst=True, errors='coerce')
df['dt_matricula'] = pd.to_datetime(df['dt_matricula'], dayfirst=True, errors='coerce')

df["tempo_permanencia"] = (df["dt_ultimo_evento"] - df["dt_matricula"]).dt.days / 365.25
df['tempo_permanencia_meses'] = (df['dt_ultimo_evento'] - df['dt_matricula']).dt.days / 30.44

# Calcular idade no DataFrame original para evitar warnings
df['dt_nascimento'] = pd.to_datetime(df['dt_nascimento'], errors='coerce')
df['idade'] = (pd.Timestamp('today') - df['dt_nascimento']).dt.days // 365

# Dicionário de dados (ajuste conforme seu dataset)
dicionario_dados = [
    {"Coluna": "sexo", "Descrição": "Sexo do aluno"},
    {"Coluna": "desc_sit_matricula", "Descrição": "Situação da matrícula (Matriculado, Concludente, Estagiario, Formado, Trancado, Abandono, Transferido e Cancelado)"},
    {"Coluna": "ano_letivo_ini", "Descrição": "Ano letivo inicial do aluno"},
    {"Coluna": "periodo_letivo_ini", "Descrição": "Semestre letivo inicial do aluno"},
    {"Coluna": "cidade", "Descrição": "Cidade de origem do aluno"},
    {"Coluna": "desc_cor", "Descrição": "Cor/raça declarada"},
    {"Coluna": "desc_tipo_escola_origem", "Descrição": "Tipo de escola de origem"},
    {"Coluna": "dt_matricula", "Descrição": "Data de matrícula"},
    {"Coluna": "dt_ultimo_evento", "Descrição": "Data do último evento de matrícula"},
    {"Coluna": "tempo_permanencia", "Descrição": "Tempo de permanência no curso (anos)"},
    {"Coluna": "tempo_permanencia_meses", "Descrição": "Tempo de permanência no curso (meses)"},
    {"Coluna": "coeficiente_rendimento", "Descrição": "Coeficiente de rendimento do aluno"},
    {"Coluna": "status", "Descrição": "cursando (Matriculado, Concludente, Estagiario), formado ou Não cursando (Trancado, Abandono, Transferido e cancelado)"},
    {"Coluna": "idade", "Descrição": "Idade do aluno"},
    # ...adicione outras colunas relevantes...
]
df_dicionario = pd.DataFrame(dicionario_dados)

# Menu de navegação
pagina = st.sidebar.radio("Navegação", ["Capa", "Análise"])

if pagina == "Capa":
    st.image(r"Data/LogoIFCE.png", width=200)
    st.title("Painel de Análise de Matrículas - Engenharia de Telecomunicações IFCE")
    st.markdown("""
    Este aplicativo foi criado com a inteção de fazer uma análise referente aos dados de matrículas do curso de Engenharia de Telecomunicações do IFCE.
    
    **Funcionalidades:**
    - Visualização do perfil dos alunos
    - Situação acadêmica atual
    - Tempo médio de permanência
    - Relação entre escola de origem e rendimento
    - Relação entre situação de matrícula e rendimento acadêmico
    
    Utilize o menu lateral para acessar as análises e aplicar filtros conforme desejar.
    """)
    st.subheader("Dicionário de Dados")
    st.dataframe(df_dicionario, use_container_width=True)

elif pagina == "Análise":
    st.title("Análise de Matrículas - Ensino Superior")

    perguntas = [
        "1). Perfil dos alunos",
        "2). Situação acadêmica atual dos alunos",
        "3). Tempo médio de permanência no curso por perfil",
        "4). Relação entre tipo de escola de origem e rendimento acadêmico",
        "5). Relação entre situação de matricula e rendimento acadêmico"
    ]
    escolha = st.sidebar.radio("Escolha uma pergunta:", perguntas)

    # =========================
    # Filtros interativos
    # =========================
    st.sidebar.header("Filtros")
    sexos = df['sexo'].dropna().unique()
    sexo_selecionado = st.sidebar.multiselect("Sexo", options=sexos, default=[])

    grupos = df['grupo'].dropna().unique()
    grupo_selecionado = st.sidebar.multiselect("Cor/raça", options=grupos, default=[])

    situacoes = df['status'].dropna().unique()
    situacao_selecionada = st.sidebar.multiselect("Situação de Matrícula", options=situacoes, default=[])

    anos = df['ano_letivo_ini'].dropna().unique()
    anos_ordenados = sorted(anos)
    anos_selecionado = st.sidebar.multiselect("Ano Letivo Inicial", options=anos_ordenados, default=[])

    semestres = df['periodo_letivo_ini'].dropna().unique()
    semestre_selecionado = st.sidebar.multiselect("Semestre Letivo Inicial", options=semestres, default=[])

    # Filtro condicional: só filtra se o usuário selecionar algo
    df_filtrado = df.copy()
    if sexo_selecionado:
        df_filtrado = df_filtrado[df_filtrado['sexo'].isin(sexo_selecionado)]
    if grupo_selecionado:
        df_filtrado = df_filtrado[df_filtrado['grupo'].isin(grupo_selecionado)]
    if situacao_selecionada:
        df_filtrado = df_filtrado[df_filtrado['status'].isin(situacao_selecionada)]
    if anos_selecionado:
        df_filtrado = df_filtrado[df_filtrado['ano_letivo_ini'].isin(anos_selecionado)]
    if semestre_selecionado:
        df_filtrado = df_filtrado[df_filtrado['periodo_letivo_ini'].isin(semestre_selecionado)]

    # =========================
    # Funções auxiliares
    # =========================
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
        total_por_x = df_grouped.groupby(x)[y].transform('sum')
        df_grouped['percent'] = (df_grouped[y] / total_por_x * 100).round(2)
        df_grouped['label'] = df_grouped.apply(lambda row: f"{row[y]} ({row['percent']}%)", axis=1)
        fig = px.bar(
            df_grouped, x=x, y=y, color=color, barmode='group',
            text='label', labels={x: x_label, y: y_label}, title=title
        )
        fig.update_traces(textposition='outside')
        return fig

    # Preparar dados para o mapa
    df_mapa = df_filtrado.value_counts("cidade").reset_index(name="frequencia")
    df_mapa["representatividade"] = (
        (df_mapa["frequencia"] / df_mapa["frequencia"].sum()) * 100
    ).round(2).astype(str) + "%"

    # Carregar o geojson local com encoding UTF-8
    geojson_url = r"geojson/geojs-23-mun.json"
    with open(geojson_url, encoding="utf-8") as f:
        geojson_data = json.load(f)

    # =========================
    # Visualizações
    # =========================
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
            st.subheader("Quantidade de matrículas")
            st.dataframe(df_mapa, height=500)

        st.subheader("Idade média dos alunos")
        st.write(f"Idade média: {df_filtrado['idade'].mean():.1f} anos")
        # Histograma de idade com representatividade
        idade_counts = df_filtrado['idade'].value_counts().sort_index()
        idade_percent = (idade_counts / idade_counts.sum() * 100).round(2)
        idade_labels = [f"{v} ({p}%)" for v, p in zip(idade_counts.values, idade_percent.values)]
        fig = px.bar(
            x=idade_counts.index, y=idade_counts.values, text=idade_labels,
            labels={'x': 'Idade', 'y': 'Quantidade'}, title="Distribuição de Idade"
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig)


        st.subheader("Distribuição por sexo")
        sexo_counts = df_filtrado['sexo'].value_counts().reset_index()
        sexo_counts.columns = ['sexo', 'quantidade']
        fig = px.pie(
            sexo_counts,
            names='sexo',
            values='quantidade',
            title="Distribuição por Sexo",
            hole=0.5,
            color='sexo',
            color_discrete_map={'F': 'red', 'M': 'blue'}
        )
        fig.update_traces(textinfo='percent+label+value')
        st.plotly_chart(fig)

        st.subheader("Evolução da proporção de sexo por ano letivo")

        # Agrupa e conta o número de alunos por ano e sexo
        sexo_ano = df_filtrado.groupby(['ano_letivo_ini', 'sexo']).size().reset_index(name='quantidade')

        # Calcula o total de alunos por ano
        total_ano = sexo_ano.groupby('ano_letivo_ini')['quantidade'].transform('sum')

        # Calcula a proporção de cada sexo em cada ano
        sexo_ano['proporcao'] = (sexo_ano['quantidade'] / total_ano * 100).round(2)

        # Cria o rótulo personalizado: "xx.x% (N)"
        sexo_ano['rotulo'] = sexo_ano['proporcao'].astype(str) + '% (' + sexo_ano['quantidade'].astype(str) + ')'

        # Gráfico de linha com rótulos e sem linhas de grade
        fig = px.line(
            sexo_ano,
            x='ano_letivo_ini',
            y='proporcao',
            color='sexo',
            markers=True,
            text='rotulo',
            labels={'ano_letivo_ini': 'Ano Letivo Inicial', 'proporcao': 'Proporção (%)', 'sexo': 'Sexo'},
            title="Proporção de Sexo por Ano Letivo",
            color_discrete_map={'F': '#E31B1F', 'M': '#0068c9'}
        )
        fig.update_traces(textposition='top center')
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        fig.update_layout(yaxis_tickformat='.1f')
        st.plotly_chart(fig)


        st.subheader("Distribuição por raça/cor")
        raca_counts = df_filtrado['grupo'].value_counts().reset_index()
        raca_counts.columns = ['grupo', 'quantidade']
        fig = px.pie(
            raca_counts,
            names='grupo',
            values='quantidade',
            title="Distribuição por Raça/Cor",
            hole=0.5,
            color='grupo',
            color_discrete_map={'PPI': 'red', 'Branca e amarela': 'blue', 'Sem informação': 'gray'}
        )
        fig.update_traces(textinfo='percent+label+value')
        st.plotly_chart(fig)

        st.subheader("Evolução da proporção de sexo por ano letivo")

        # Agrupa e conta o número de alunos por ano e sexo
        grupo_ano = df_filtrado.groupby(['ano_letivo_ini', 'grupo']).size().reset_index(name='quantidade')

        # Calcula o total de alunos por ano
        total_ano = grupo_ano.groupby('ano_letivo_ini')['quantidade'].transform('sum')

        # Calcula a proporção de cada sexo em cada ano
        grupo_ano['proporcao'] = (grupo_ano['quantidade'] / total_ano * 100).round(2)

        # Cria o rótulo personalizado: "xx.x% (N)"
        grupo_ano['rotulo'] = grupo_ano['proporcao'].astype(str) + '% (' + grupo_ano['quantidade'].astype(str) + ')'

        # Gráfico de linha com rótulos e sem linhas de grade
        fig = px.line(
            grupo_ano,
            x='ano_letivo_ini',
            y='proporcao',
            color='grupo',
            markers=True,
            text='rotulo',
            labels={'ano_letivo_ini': 'Ano Letivo Inicial', 'proporcao': 'Proporção (%)', 'grupo': 'Cor/Raça'},
            title="Proporção de cor/raça por Ano Letivo",
            color_discrete_map={'PPI': '#E31B1F', 'Branca e amarela': '#0068c9', 'Sem informação': 'gray'}
        )
        fig.update_traces(textposition='top center')
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        fig.update_layout(yaxis_tickformat='.1f')
        st.plotly_chart(fig)

        st.subheader("Distribuição por cor/raça")
        cor_counts = df_filtrado['desc_cor'].value_counts()
        st.plotly_chart(bar_with_percent(cor_counts, 'Cor/Raça', 'Quantidade', "Cor/Raça"))

        st.subheader("Tipo de escola de origem")
        escola_counts = df_filtrado['desc_tipo_escola_origem'].value_counts()
        st.plotly_chart(bar_with_percent(escola_counts, 'Tipo de Escola', 'Quantidade', "Tipo de Escola de Origem"))

    elif escolha == perguntas[1]:
        st.header("2. Situação acadêmica atual dos alunos")


        st.subheader("Abandono por letivo inicial")
        ult_per_counts = df_filtrado[df_filtrado['desc_sit_matricula'] == "Abandono"]['ano_letivo_ini'].value_counts()
        st.plotly_chart(bar_with_percent(ult_per_counts, 'Ano letivo', 'Quantidade', "Abandono por Período Letivo Inicial"))

        st.subheader("Cursando por ano letivo inicial")
        per_counts = df_filtrado[df_filtrado['desc_sit_matricula'] == "Matriculado"]['ano_letivo_ini'].value_counts()
        st.plotly_chart(bar_with_percent(per_counts, 'Situação no Período', 'Quantidade', "Cursando por ano letivo inicial"))

        st.subheader("Distribuição matriculas por situação")
        raca_counts = df_filtrado['status'].value_counts().reset_index()
        raca_counts.columns = ['status', 'quantidade']
        fig = px.pie(
            raca_counts,
            names='status',
            values='quantidade',
            title="Distribuição por Situação Acadêmica",
            hole=0.5,
            color='status',
            color_discrete_map={
                'Sem êxito': "#E31B1F",
                'Matriculado': "#0068c9",
                'Egresso': 'green'
            },
        )
        fig.update_traces(textinfo='percent+label+value')
        st.plotly_chart(fig)

        st.subheader("Status dos alunos por Ano Letivo Inicial")

        # Agrupa e conta
        status_ano = df_filtrado.groupby(['ano_letivo_ini', 'status']).size().reset_index(name='quantidade')

        # Calcula o total por ano
        total_por_ano = status_ano.groupby('ano_letivo_ini')['quantidade'].transform('sum')
        status_ano['percentual'] = (status_ano['quantidade'] / total_por_ano * 100).round(1)
        status_ano['label'] = status_ano['percentual'].astype(str) + '%'

        fig = px.bar(
            status_ano,
            x='ano_letivo_ini',
            y='quantidade',
            color='status',
            title="Distribuição do Status dos Alunos por Ano Letivo Inicial",
            labels={'ano_letivo_ini': 'Ano Letivo Inicial', 'quantidade': 'Quantidade', 'status': 'Status'},
            barmode='stack',
            color_discrete_map={
                'Sem êxito': "#E31B1F",
                'Matriculado': "#0068c9",
                'Egresso': 'green'
            },
            text='label'
        )
        fig.update_traces(textposition='outside', textangle=0)
        st.plotly_chart(fig)

    elif escolha == perguntas[2]:
        st.header("3. Tempo médio de permanência no curso por perfil")

        st.subheader("Tempo médio de permanência (em anos)")
        st.write(f"Tempo médio: {df_filtrado['tempo_permanencia'].mean():.1f} anos")

        st.subheader("Tempo de permanência por sexo")
        fig = px.box(
            df_filtrado, x='sexo', y='tempo_permanencia', color='sexo',
            points="all", title="Tempo de Permanência por Sexo"
        )
        st.plotly_chart(fig)

        st.subheader("Tempo de permanência por tipo de escola de origem")
        fig = px.box(
            df_filtrado, x='desc_tipo_escola_origem', y='tempo_permanencia', color='desc_tipo_escola_origem',
            points="all", title="Tempo de Permanência por Tipo de Escola de Origem"
        )
        st.plotly_chart(fig)

        st.subheader("Tempo de permanência por situação da matrícula")
        fig = px.box(
            df_filtrado, x='status', y='tempo_permanencia', color='status',
            points="all", title="Tempo de Permanência por Situação da Matrícula"
        )
        st.plotly_chart(fig)

    elif escolha == perguntas[3]:
        st.header("4. Relação entre tipo de escola de origem e rendimento acadêmico")

        st.subheader("Coeficiente de rendimento por tipo de escola de origem")
        fig = px.box(
            df_filtrado, x='desc_tipo_escola_origem', y='coeficiente_rendimento', color='desc_tipo_escola_origem',
            points="all", title="Coeficiente de Rendimento por Tipo de Escola de Origem"
        )
        st.plotly_chart(fig)

    elif escolha == perguntas[4]:
        st.header("5. Relação entre situação de matricula e rendimento acadêmico")


        st.subheader("Coeficiente de rendimento por situação de matricula.")
        fig = px.box(
            df_filtrado, x='status', y='coeficiente_rendimento', color='status',
            points="all", title="Coeficiente de Rendimento por Situação de Matrícula"
        )
        st.plotly_chart(fig)