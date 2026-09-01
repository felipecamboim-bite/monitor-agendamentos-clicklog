from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import Client, create_client

# Configuração da página em layout amplo
st.set_page_config(
    page_title="Monitor de Agendamentos - ClickLog", layout="wide"
)

# Estilização visual: Cards compactos, centralizados e tema escuro
st.markdown(
    """
    <style>
    /* Força o tema escuro em toda a aplicação, ignorando o modo do navegador */
    .stApp, .main, [data-testid="stHeader"], [data-testid="stToolbar"] {
        background-color: #0e1117 !important;
        color: #ffffff !important;
    }
    .stMetric { 
        background-color: #1e1e1e !important; 
        padding: 10px; 
        border-radius: 8px; 
        border: 1px solid #333333; 
        text-align: center;
    }
    .stMetric label { 
        display: block; 
        text-align: center; 
        color: #b0b0b0 !important;
    }
    .stMetric [data-testid="stMetricValue"] { 
        justify-content: center; 
        color: #ffffff !important;
    }
    div[data-baseweb="select"] > div { 
        background-color: #1e1e1e !important; 
        color: #ffffff !important;
    }
    .card-hoje {
        background-color: #1e1e1e !important;
        border: 1px solid #333333 !important;
        padding: 15px;
        border-radius: 8px;
        height: 100%;
        color: #ffffff !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📊 Monitor de Agendamentos - ClickLog")
st.markdown(
    "Painel em tempo real integrado ao Supabase para acompanhamento operacional."
)

# Suas credenciais do Supabase
SUPABASE_URL = "https://dmucssgskmhpqdkyovwc.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im"
    "RtdWNzc2dza21ocHFka3lvdndjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4"
    "MTEwMjU1NSwiZXhwIjoyMDk2Njc4NTU1fQ.gLBIHNI8tyq6DGnzlXwnMrmNubRylbeR66zq71NNrMw"
)


@st.cache_data(ttl=30)
def carregar_dados():
  supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
  response = supabase.table("agendamentos").select("*").execute()
  return pd.DataFrame(response.data)


df = carregar_dados()


# Função para formatar números grandes (K, Mi, Bi)
def formata_numero(valor):
  if pd.isna(valor):
    return "0"
  if valor >= 1_000_000_000:
    return f"{valor / 1_000_000_000:.2f}bi".replace(".", ",")
  elif valor >= 1_000_000:
    return f"{valor / 1_000_000:.2f}mi".replace(".", ",")
  elif valor >= 1_000:
    return f"{valor / 1_000:.2f}k".replace(".", ",")
  else:
    return str(int(valor))


if not df.empty:
  # Tratamento e conversão de datas e colunas
  df["data_dt"] = pd.to_datetime(df["data_prevista"], errors="coerce")
  df["Ano"] = df["data_dt"].dt.year
  df["Mês"] = df["data_dt"].dt.month
  df["Dia_Str"] = df["data_dt"].dt.strftime("%d/%m/%Y")

  if "volumetria" not in df.columns:
    df["volumetria"] = 1

  # Detectar coluna de notas
  coluna_notas = None
  for c in ["notas", "nota", "nf", "documento"]:
    if c in df.columns:
      coluna_notas = c
      break

  # --- BLOCO DE FILTROS NA TELA ---
  st.markdown("### ⚙️ Filtros Globais do Dashboard")
  f_col1, f_col2, f_col3, f_col4 = st.columns(4)

  with f_col1:
    anos_disp = sorted([str(x) for x in df["Ano"].dropna().unique()])
    filtro_ano = st.multiselect("Filtrar Ano", anos_disp)

  with f_col2:
    meses_disp = [
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
    ]
    filtro_mes = st.multiselect("Filtrar Mês", meses_disp)

  with f_col3:
    datas_disp = sorted(df["Dia_Str"].dropna().unique().tolist())
    filtro_data = st.multiselect("Filtrar Data Específica", datas_disp)

  with f_col4:
    empresas_disp = sorted(
        df["empresa"].dropna().unique().tolist()
        if "empresa" in df.columns
        else []
    )
    filtro_empresa = st.multiselect("Filtrar Empresa", empresas_disp)

  st.markdown("---")

  # --- SEÇÃO SUPERIOR: Invertido (Bloco do Dia na Esquerda, Totais na Direita) ---
  col_hoje, col_card1, col_card2 = st.columns([3, 1.5, 1.5])

  with col_hoje:
    # Filtrando dados estritamente para o dia de hoje
    hoje_str = datetime.now().strftime("%d/%m/%Y")
    df_hoje = df[df["Dia_Str"] == hoje_str]

    vol_hoje = df_hoje["volumetria"].sum() if not df_hoje.empty else 0
    notas_hoje = (
        df_hoje[coluna_notas].nunique()
        if (not df_hoje.empty and coluna_notas)
        else len(df_hoje)
    )
    empresas_hoje = (
        df_hoje["empresa"].dropna().unique().tolist()
        if (not df_hoje.empty and "empresa" in df_hoje.columns)
        else []
    )

    st.markdown(
        f"""
        <div class="card-hoje">
            <h4 style="margin: 0 0 10px 0; color: #ffffff; font-size: 16px;">📌 Agendamentos do Dia ({hoje_str})</h4>
            <p style="margin: 4px 0; color: #b0b0b0; font-size: 14px;"><b>Volumes:</b> {formata_numero(vol_hoje)} &nbsp;|&nbsp; <b>Notas:</b> {formata_numero(notas_hoje)}</p>
            <p style="margin: 8px 0 2px 0; color: #b0b0b0; font-size: 13px;"><b>Empresas com agenda hoje:</b></p>
            <p style="margin: 0; color: #ffffff; font-size: 13px;">{', '.join(empresas_hoje) if empresas_hoje else 'Nenhuma empresa agendada para hoje.'}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col_card1:
    vol_total_geral = df["volumetria"].sum()
    st.metric("Total de Volumes", formata_numero(vol_total_geral))

  with col_card2:
    total_notas_geral = (
        df[coluna_notas].nunique() if coluna_notas else len(df)
    )
    st.metric("Total de Notas", formata_numero(total_notas_geral))

  st.markdown("---")

  # --- APLICANDO OS FILTROS PARA OS GRÁFICOS (Foco padrão em Ago/Set se nada for marcado) ---
  df_filtrado = df.copy()

  if not filtro_mes:
    df_filtrado = df_filtrado[df_filtrado["Mês"].isin([8, 9])]

  if filtro_ano:
    df_filtrado = df_filtrado[df_filtrado["Ano"].astype(str).isin(filtro_ano)]
  if filtro_mes:
    df_filtrado = df_filtrado[
        df_filtrado["Mês"].apply(lambda x: f"{int(x):02d}").isin(filtro_mes)
    ]
  if filtro_data:
    df_filtrado = df_filtrado[df_filtrado["Dia_Str"].isin(filtro_data)]
  if filtro_empresa:
    df_filtrado = df_filtrado[df_filtrado["empresa"].isin(filtro_empresa)]

  # --- GRÁFICO 1: Diário (Degradê Azul) ---
  st.subheader("📅 Volumetria por Data Prevista (Diário)")
  df_diario = (
      df_filtrado.groupby(["data_dt", "Dia_Str"])["volumetria"]
      .sum()
      .reset_index()
  )
  df_diario = df_diario.sort_values("data_dt")

  fig_diario = px.bar(
      df_diario,
      x="Dia_Str",
      y="volumetria",
      text="volumetria",
      color="volumetria",
      color_continuous_scale="Blues",
      labels={"Dia_Str": "Data Prevista", "volumetria": "Volume"},
  )
  fig_diario.update_traces(textposition="outside")
  fig_diario.update_layout(
      xaxis_type="category",
      xaxis_tickangle=-45,
      margin=dict(t=30, b=30),
      coloraxis_showscale=False,
  )
  st.plotly_chart(fig_diario, width="stretch")

  st.markdown("---")

  c1, c2 = st.columns(2)

  with c1:
    # --- GRÁFICO 2: Mensal (Degradê Azul) ---
    st.subheader("📈 Volumetria Mensal")
    df_mensal = df_filtrado.groupby("Mês")["volumetria"].sum().reset_index()
    meses_dict = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez",
    }
    df_mensal["Nome_Mes"] = df_mensal["Mês"].map(meses_dict)
    df_mensal = df_mensal.sort_values("Mês")

    fig_mensal = px.bar(
        df_mensal,
        x="Nome_Mes",
        y="volumetria",
        text="volumetria",
        color="volumetria",
        color_continuous_scale="Blues",
        labels={"Nome_Mes": "Mês", "volumetria": "Volume"},
    )
    fig_mensal.update_traces(textposition="outside")
    fig_mensal.update_layout(
        xaxis_type="category",
        margin=dict(t=30, b=30),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_mensal, width="stretch")

  with c2:
    # --- GRÁFICO 3: Turno (Rosca em tons de azul) ---
    st.subheader("🕒 Volumetria por Turno")
    if "turno" in df_filtrado.columns:
      df_turno = df_filtrado.groupby("turno")["volumetria"].sum().reset_index()
      fig_turno = px.pie(
          df_turno,
          names="turno",
          values="volumetria",
          hole=0.4,
          color_discrete_sequence=px.colors.sequential.Blues_r,
      )
      fig_turno.update_layout(margin=dict(t=30, b=30))
      st.plotly_chart(fig_turno, width="stretch")
    else:
      st.warning("Coluna 'turno' não encontrada na tabela.")

  st.markdown("---")

  # --- GRÁFICO 4: Ranking de Empresas (Alinhado à esquerda + Degradê Azul) ---
  st.subheader("🏆 Ranking de Empresas (Maior Volume)")
  if "empresa" in df_filtrado.columns:
    df_empresa = (
        df_filtrado.groupby("empresa")["volumetria"]
        .sum()
        .reset_index()
        .sort_values(by="volumetria", ascending=True)
    )

    fig_empresa = px.bar(
        df_empresa,
        x="volumetria",
        y="empresa",
        orientation="h",
        text="volumetria",
        color="volumetria",
        color_continuous_scale="Blues",
        labels={"empresa": "Empresa", "volumetria": "Volume"},
    )
    fig_empresa.update_traces(textposition="outside")
    fig_empresa.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin=dict(t=30, b=30),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_empresa, width="stretch")
  else:
    st.warning("Coluna 'empresa' não encontrada na tabela.")

else:
  st.warning("A tabela de agendamentos está vazia ou não pôde ser lida.")