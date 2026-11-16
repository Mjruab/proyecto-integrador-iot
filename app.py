"""Dashboard del tótem IoT de monitoreo fisiológico (EAFIT) - datos sintéticos.

Ejecutar localmente:  streamlit run app.py
"""
import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

CSV_PATH = Path(__file__).parent / "proyecto_integrador_eafit_max30102.csv"
TZ = "America/Bogota"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
ESTADOS = {"Todas": None, "Solo válidas": "valid", "Solo inválidas": "invalid"}

# Paleta (inspirada en ilustraciones planas con textura granulada)
CREMA, NAVY, AZUL, MOSTAZA = "#FFF6DD", "#2F4A74", "#3A6FD8", "#F2A900"
ROJO, VERDE, AMARILLO = "#E5484D", "#4CB26B", "#FFD23F"
# Color base -> tono oscuro para los "puntitos" del grano en las barras
GRANO = {AZUL: "#1E3F8F", MOSTAZA: "#B87400", ROJO: "#9B1F27", VERDE: "#2B7A45", NAVY: "#16263F"}

st.set_page_config(page_title="Tótem IoT EAFIT", page_icon="🫀", layout="wide")


# --------------------------------------------------------------------------- #
# Estilo visual (CSS + ilustración SVG propia)
# --------------------------------------------------------------------------- #
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=DM+Sans:wght@400;500;700&display=swap');

html, body, [class*="css"], .stApp { font-family: 'DM Sans', sans-serif; color: #2F4A74; }
.stApp {
  background-color: #FFF6DD;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .18  0 0 0 0 .29  0 0 0 0 .45  0 0 0 1.1 -.42'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='.55'/></svg>");
}
h1, h2, h3, h4 { font-family: 'Fraunces', serif !important; color: #2F4A74 !important; letter-spacing: -.01em; }
.block-container { padding-top: 1.6rem; max-width: 1280px; }
header[data-testid="stHeader"] { background: transparent; }

/* Barra lateral */
[data-testid="stSidebar"] { background-color: #FFD23F;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .72  0 0 0 0 .45  0 0 0 0 0  0 0 0 1.2 -.45'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='.6'/></svg>");
  border-right: 3px solid #2F4A74; }
[data-testid="stSidebar"] * { color: #2F4A74; }

/* Tarjetas: contenedores con borde */
[data-testid="stVerticalBlockBorderWrapper"] { background: rgba(255,255,255,.72); border: 2.5px solid #2F4A74 !important;
  border-radius: 22px !important; box-shadow: 5px 5px 0 #2F4A74; padding: .35rem .5rem; }

/* Indicadores */
[data-testid="stMetric"] { background: #fff; border: 2.5px solid #2F4A74; border-radius: 20px; padding: 14px 18px;
  box-shadow: 4px 4px 0 #2F4A74; }
[data-testid="stMetricLabel"] p { font-weight: 700; font-size: .92rem; white-space: normal !important; }
[data-testid="stMetricLabel"] { overflow: visible; }
[data-testid="stMetricValue"] > div { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }
[data-testid="stMetricValue"] { font-family: 'Fraunces', serif; font-weight: 800; color: #2F4A74; }
div[data-testid="stColumn"]:nth-child(1) [data-testid="stMetric"] { background: #FFD23F; }
div[data-testid="stColumn"]:nth-child(5) [data-testid="stMetric"] { background: #FFC9C6; }

/* Pestañas */
[role="tablist"] { gap: 4px; border-bottom: 3px solid #2F4A74 !important; flex-wrap: wrap; padding-left: 6px; }
[role="tab"] { background: rgba(255,255,255,.55) !important; border: none !important; border-radius: 18px 18px 0 0 !important;
  padding: 8px 20px; height: auto; margin-bottom: -3px; box-shadow: none !important; }
[role="tab"]:hover { background: #fff !important; }
[role="tab"] p { font-weight: 700; font-size: .98rem; }
[role="tab"][aria-selected="true"] { background: #2F4A74 !important; }
[role="tab"][aria-selected="true"] p { color: #FFF6DD !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"], [data-testid="stTabs"] [role="tablist"] + div[aria-hidden] { display: none !important; }

/* Textos de apoyo */
.titulo-g { font-family: 'Fraunces', serif; font-weight: 800; font-size: 1.15rem; margin: .2rem 0 .1rem; }
.nota { background: #FFF1B8; border: 2px dashed #2F4A74; border-radius: 14px; padding: 10px 14px; font-size: .92rem; line-height: 1.45; margin: .3rem 0 .6rem; }
.hero-sub { font-size: 1.05rem; max-width: 640px; line-height: 1.5; }
.chip { display: inline-block; background: #2F4A74; color: #FFF6DD !important; border-radius: 999px; padding: 3px 12px; font-size: .8rem; font-weight: 700; margin: 0 6px 6px 0; }
.informe { background: #fff; border: 2.5px solid #2F4A74; border-radius: 18px; padding: 6px 20px 8px; box-shadow: 4px 4px 0 #3A6FD8; }
.informe li { margin: .45rem 0; line-height: 1.5; }
.hallazgo-n { display:inline-block; background:#F2A900; border:2px solid #2F4A74; border-radius:50%; width:34px; height:34px; text-align:center; line-height:30px; font-weight:800; margin-right:8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def ilustracion_totem() -> str:
    """Ilustración original (SVG) del tótem, con textura granulada. Se incrusta como imagen base64."""
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 460 420'>
<defs>
 <filter id='grano' x='0' y='0' width='100%' height='100%'>
  <feTurbulence type='fractalNoise' baseFrequency='.95' numOctaves='2' result='n'/>
  <feColorMatrix in='n' type='matrix' values='0 0 0 0 .1  0 0 0 0 .16  0 0 0 0 .3  0 0 0 -1.4 .85' result='g'/>
  <feComposite in='g' in2='SourceGraphic' operator='in' result='gs'/>
  <feMerge><feMergeNode in='SourceGraphic'/><feMergeNode in='gs'/></feMerge>
 </filter>
</defs>
<g filter='url(#grano)'>
 <circle cx='235' cy='190' r='150' fill='#CFE0F5'/>
 <path d='M70 390 L155 118 Q165 88 195 88 L275 88 Q305 88 315 118 L400 390 Z' fill='#8BA9D1'/>
 <rect x='150' y='70' width='160' height='320' rx='28' fill='{NAVY}'/>
 <rect x='168' y='92' width='124' height='100' rx='16' fill='{AMARILLO}'/>
 <polyline points='178,150 205,150 217,120 234,176 248,138 258,150 282,150' fill='none' stroke='{ROJO}' stroke-width='7' stroke-linecap='round' stroke-linejoin='round'/>
 <rect x='168' y='210' width='124' height='62' rx='14' fill='{MOSTAZA}'/>
 <circle cx='230' cy='241' r='20' fill='{ROJO}' stroke='{NAVY}' stroke-width='5'/>
 <circle cx='230' cy='241' r='8' fill='#FFE2E0'/>
 <rect x='168' y='292' width='124' height='34' rx='12' fill='{AZUL}'/>
 <path d='M190 309 q12 -14 24 0 M200 309 q2 -6 4 0' fill='none' stroke='#fff' stroke-width='4' stroke-linecap='round'/>
 <rect x='60' y='384' width='340' height='26' rx='13' fill='#1E3358'/>
 <circle cx='86' cy='110' r='10' fill='{MOSTAZA}'/><circle cx='392' cy='96' r='7' fill='{AZUL}'/>
 <circle cx='370' cy='250' r='12' fill='{VERDE}'/><circle cx='62' cy='270' r='8' fill='{ROJO}'/>
 <path d='M365 150 l6 14 14 6 -14 6 -6 14 -6 -14 -14 -6 14 -6z' fill='{AMARILLO}' stroke='{NAVY}' stroke-width='3'/>
</g></svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def estilo(fig: go.Figure, alto: int = 340) -> go.Figure:
    """Estilo común de todas las gráficas."""
    fig.update_layout(
        template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.0)",
        font=dict(family="DM Sans, sans-serif", color=NAVY, size=13), height=alto,
        margin=dict(t=10, l=10, r=10, b=10), legend_title_text="",
        hoverlabel=dict(bgcolor="white", font_family="DM Sans"),
    )
    fig.update_xaxes(gridcolor="rgba(47,74,116,.12)", linecolor=NAVY, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(47,74,116,.12)", linecolor=NAVY, zeroline=False)
    return fig


def granular(fig: go.Figure, tam: int = 3, solidez: float = 0.4) -> go.Figure:
    """Da textura de puntitos (grano) a las barras e histogramas."""
    for tr in fig.data:
        if tr.type in ("bar", "histogram") and isinstance(tr.marker.color, str) and tr.marker.color in GRANO:
            base = tr.marker.color
            tr.marker.pattern = dict(shape=".", size=tam, solidity=solidez, bgcolor=base, fgcolor=GRANO[base])
            tr.marker.line = dict(color=GRANO[base], width=1.5)
    return fig


def tarjeta(titulo: str, fig: go.Figure, como: str, lectura: str = "") -> None:
    """Gráfica + título + explicación (cómo leerla y qué muestra con los filtros actuales)."""
    with st.container(border=True):
        st.markdown(f'<div class="titulo-g">{titulo}</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, width="stretch")
        extra = f"<br><b>📌 Lo que muestra ahora.</b> {lectura}" if lectura else ""
        st.markdown(f'<div class="nota"><b>🔎 Cómo leerla.</b> {como}{extra}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Carga y preparación de datos
# --------------------------------------------------------------------------- #
@st.cache_data
def cargar_datos() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    # Las marcas de tiempo vienen en UTC: se convierten a hora de Colombia
    # y luego se quita la zona horaria para que Plotly no las vuelva a mover.
    ts = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(TZ)
    df["timestamp"] = ts.dt.tz_localize(None)
    df["fecha"] = df["timestamp"].dt.normalize()
    df["hora"] = df["timestamp"].dt.hour
    df["dia_semana"] = df["timestamp"].dt.dayofweek          # 0 = lunes
    df["dia_nombre"] = df["dia_semana"].map(dict(enumerate(DIAS)))
    df["es_fin_de_semana"] = df["dia_semana"] >= 5
    df["estado_valido"] = df["measurement_status"].eq("valid")
    return df.sort_values("timestamp").reset_index(drop=True)


def limites_iqr(serie: pd.Series) -> tuple[float, float]:
    """Límites estadísticos (1.5 x IQR) para marcar valores atípicos."""
    q1, q3 = serie.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def pct(parte: float, total: float) -> float:
    return 100 * parte / total if total else 0.0


def fmt_fecha(ts: pd.Timestamp) -> str:
    return ts.strftime("%d/%m/%Y")


df_all = cargar_datos()
validas_all = df_all[df_all["estado_valido"]]

# --------------------------------------------------------------------------- #
# Filtros (barra lateral)
# --------------------------------------------------------------------------- #
st.sidebar.markdown("## Filtros")
f_min, f_max = df_all["fecha"].min().date(), df_all["fecha"].max().date()

rango = st.sidebar.date_input("Rango de fechas", value=(f_min, f_max), min_value=f_min, max_value=f_max)
# Mientras el usuario elige la fecha final, date_input devuelve una sola fecha
f_ini, f_fin = (rango[0], rango[1]) if len(rango) == 2 else (rango[0], rango[0])

estudiante = st.sidebar.selectbox("Estudiante", ["Todos"] + sorted(df_all["student_id"].unique()))
estado_label = st.sidebar.radio("Estado de la medición", list(ESTADOS))
estado = ESTADOS[estado_label]

# Base con fecha + estado (sin estudiante): se usa en el seguimiento individual
base = df_all[(df_all["fecha"].dt.date >= f_ini) & (df_all["fecha"].dt.date <= f_fin)]
if estado:
    base = base[base["measurement_status"] == estado]
df = base if estudiante == "Todos" else base[base["student_id"] == estudiante]

st.sidebar.markdown(
    f"**{len(df):,}** de {len(df_all):,} mediciones con los filtros actuales.\n\n"
    "Datos **sintéticos**. Las horas se muestran en hora de Colombia (UTC-5)."
)

# --------------------------------------------------------------------------- #
# Encabezado
# --------------------------------------------------------------------------- #
c_txt, c_img = st.columns([1.5, 1])
with c_txt:
    st.markdown(
        '<span class="chip">Computación Física e IoT</span><span class="chip">EAFIT</span>'
        '<span class="chip">Datos sintéticos</span>',
        unsafe_allow_html=True,
    )
    st.title("Tótem IoT de monitoreo fisiológico")
    st.markdown(
        '<p class="hero-sub">Cada vez que un estudiante apoya el dedo en el tótem, queda registrada su '
        'frecuencia cardíaca y su saturación de oxígeno. Aquí convertimos esos registros en historias: '
        '<b>cuándo se usa el tótem</b>, <b>qué valores aparecen</b> y <b>qué tan confiables son los datos</b>.</p>',
        unsafe_allow_html=True,
    )
    with st.expander("📖 Guía rápida: ¿qué significan BPM y SpO₂?"):
        st.markdown(
            "- **BPM** son los *latidos por minuto*: cuántas veces late el corazón en un minuto.\n"
            "- **SpO₂** es el *porcentaje estimado de oxígeno en la sangre*, medido con luz en la yema del dedo.\n"
            "- **Medición válida / inválida**: el tótem marca cada lectura. Los promedios usan solo las válidas.\n"
            "- **Atípico**: un valor muy lejos de lo habitual del grupo. Es un criterio *estadístico*, no médico.\n\n"
            "⚠️ Estos datos son simulados y el sensor es educativo: no sirven para evaluar la salud de nadie."
        )
with c_img:
    st.markdown(f'<img src="{ilustracion_totem()}" style="width:100%;max-width:380px;display:block;margin:auto">',
                unsafe_allow_html=True)

if df.empty:
    st.warning("No hay mediciones con los filtros seleccionados. Amplía el rango de fechas o cambia el estado.")
    st.stop()

# --------------------------------------------------------------------------- #
# Indicadores generales
# --------------------------------------------------------------------------- #
validas = df[df["estado_valido"]]
n_total = len(df)
n_inval = int((~df["estado_valido"]).sum())

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Mediciones", f"{n_total:,}")
k2.metric("Estudiantes", f"{df['student_id'].nunique():,}", help="Estudiantes distintos que usaron el tótem")
k3.metric("BPM promedio", f"{validas['heart_rate_bpm'].mean():.1f}" if len(validas) else "—")
k4.metric("SpO₂ promedio", f"{validas['spo2_percent'].mean():.1f} %" if len(validas) else "—")
k5.metric("Mediciones inválidas", f"{n_inval:,}", f"{pct(n_inval, n_total):.1f} % del total",
          delta_color="off", delta_arrow="off")
st.caption("Los promedios de BPM y SpO₂ usan solo las mediciones válidas. Los indicadores cambian con los filtros.")

tab_uso, tab_fisio, tab_ind, tab_cal, tab_hall = st.tabs(
    ["📈 Uso del tótem", "❤️ Indicadores fisiológicos", "👤 Seguimiento individual",
     "🧪 Calidad de datos", "💡 Hallazgos"]
)

# --------------------------------------------------------------------------- #
# 1. Uso del tótem
# --------------------------------------------------------------------------- #
with tab_uso:
    por_dia = df.groupby("fecha").agg(
        mediciones=("student_id", "size"), fin_de_semana=("es_fin_de_semana", "first")).reset_index()
    por_dia["Tipo de día"] = por_dia["fin_de_semana"].map({True: "Fin de semana", False: "Entre semana"})
    fig = px.bar(por_dia, x="fecha", y="mediciones", color="Tipo de día",
                 color_discrete_map={"Entre semana": AZUL, "Fin de semana": MOSTAZA},
                 labels={"fecha": "Fecha", "mediciones": "Mediciones"})
    fig.update_layout(legend=dict(orientation="h", y=1.12))
    top_dia = por_dia.loc[por_dia["mediciones"].idxmax()]
    lect = f"El día más movido fue el {fmt_fecha(top_dia['fecha'])} con {top_dia['mediciones']} mediciones. "
    sem, fin = por_dia[~por_dia["fin_de_semana"]]["mediciones"], por_dia[por_dia["fin_de_semana"]]["mediciones"]
    if len(sem) and len(fin):
        lect += f"Entre semana hay en promedio {sem.mean():.0f} mediciones al día; en fin de semana, {fin.mean():.0f}."
    tarjeta("Mediciones por día", granular(estilo(fig, 320)),
            "Cada barra es un día. Cuanto más alta, más estudiantes usaron el tótem ese día. "
            "Las barras azules son días entre semana y las mostaza, sábados y domingos.", lect)

    c1, c2 = st.columns(2)
    with c1:
        por_hora = df.groupby("hora").size().reset_index(name="mediciones")
        fig = px.bar(por_hora, x="hora", y="mediciones", labels={"hora": "Hora del día", "mediciones": "Mediciones"})
        fig.update_traces(marker_color=AZUL)
        fig.update_xaxes(dtick=1)
        h_max, h_min = por_hora.loc[por_hora["mediciones"].idxmax()], por_hora.loc[por_hora["mediciones"].idxmin()]
        tarjeta("¿A qué horas se usa?", granular(estilo(fig)),
                "Eje horizontal: la hora del día (formato 24 horas, hora de Colombia). Eje vertical: cuántas mediciones "
                "se hicieron en esa hora sumando todos los días.",
                f"La hora con más mediciones fue las {int(h_max['hora'])}h ({h_max['mediciones']}) y la que menos, "
                f"las {int(h_min['hora'])}h ({h_min['mediciones']}).")
    with c2:
        mapa = df.pivot_table(index="dia_semana", columns="hora", values="student_id",
                              aggfunc="size", fill_value=0).reindex(range(7), fill_value=0)
        fig = px.imshow(mapa.values, x=[f"{h}h" for h in mapa.columns], y=DIAS, aspect="auto",
                        color_continuous_scale=[CREMA, AMARILLO, MOSTAZA, "#B8470B"],
                        labels=dict(color="Mediciones"))
        pico = mapa.stack().idxmax()
        tarjeta("Mapa de calor: día × hora", estilo(fig),
                "Cada casilla cruza un día de la semana (filas) con una hora (columnas). "
                "Cuanto más oscuro el color, más mediciones se acumularon en esa combinación.",
                f"La casilla más intensa es {DIAS[pico[0]].lower()} a las {pico[1]}h "
                f"({int(mapa.loc[pico])} mediciones). Los sábados y domingos se ven casi vacíos.")

    por_est = df.groupby("student_id").size().rename("mediciones").reset_index()
    c3, c4 = st.columns(2)
    with c3:
        fig = px.histogram(por_est, x="mediciones", nbins=20, labels={"mediciones": "Mediciones por estudiante"})
        fig.update_traces(marker_color=MOSTAZA)
        fig.update_layout(yaxis_title="Número de estudiantes")
        tarjeta("¿Qué tan seguido lo usa cada estudiante?", granular(estilo(fig)),
                "Agrupa a los estudiantes según cuántas veces se midieron. Una barra alta a la izquierda significa "
                "muchos estudiantes con pocas mediciones; hacia la derecha están los más constantes.",
                f"La mitad de los estudiantes se midió {por_est['mediciones'].median():.0f} veces o menos; "
                f"{int((por_est['mediciones'] == 1).sum())} lo usaron una sola vez.")
    with c4:
        top = por_est.nlargest(15, "mediciones").sort_values("mediciones")
        fig = px.bar(top, x="mediciones", y="student_id", orientation="h",
                     labels={"mediciones": "Mediciones", "student_id": ""})
        fig.update_traces(marker_color=AZUL)
        mejor = top.iloc[-1]
        tarjeta("Los 15 estudiantes más constantes", granular(estilo(fig)),
                "Cada barra es un estudiante (identificador ficticio) y su largo, el número de veces que usó el tótem.",
                f"{mejor['student_id']} lidera con {mejor['mediciones']} mediciones; el puesto 15 tiene {top.iloc[0]['mediciones']}.")

# --------------------------------------------------------------------------- #
# 2. Indicadores fisiológicos (solo mediciones válidas)
# --------------------------------------------------------------------------- #
with tab_fisio:
    st.caption("Estas gráficas usan únicamente mediciones **válidas** dentro de los filtros aplicados.")
    if validas.empty:
        st.info("No hay mediciones válidas con los filtros actuales.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(validas, x="heart_rate_bpm", nbins=40, labels={"heart_rate_bpm": "Latidos por minuto (BPM)"})
            fig.update_traces(marker_color=AZUL)
            fig.add_vline(x=validas["heart_rate_bpm"].mean(), line_dash="dash", line_color=ROJO, line_width=3,
                          annotation_text=f"Promedio {validas['heart_rate_bpm'].mean():.1f}")
            fig.update_layout(yaxis_title="Mediciones")
            q1, q3 = validas["heart_rate_bpm"].quantile([.25, .75])
            tarjeta("Distribución de la frecuencia cardíaca", granular(estilo(fig)),
                    "Muestra qué valores de BPM son más comunes: cada barra cuenta cuántas mediciones cayeron en ese rango. "
                    "Una montaña alta y estrecha indica valores muy parecidos entre sí. La línea roja marca el promedio.",
                    f"La mitad central de las mediciones está entre {q1:.0f} y {q3:.0f} BPM. "
                    f"El mínimo fue {validas['heart_rate_bpm'].min()} y el máximo {validas['heart_rate_bpm'].max()}.")
        with c2:
            fig = px.histogram(validas, x="spo2_percent", nbins=40, labels={"spo2_percent": "Saturación de oxígeno (%)"})
            fig.update_traces(marker_color=VERDE)
            fig.add_vline(x=validas["spo2_percent"].mean(), line_dash="dash", line_color=ROJO, line_width=3,
                          annotation_text=f"Promedio {validas['spo2_percent'].mean():.1f}")
            fig.update_layout(yaxis_title="Mediciones")
            q1, q3 = validas["spo2_percent"].quantile([.25, .75])
            tarjeta("Distribución de la saturación de oxígeno", granular(estilo(fig)),
                    "Igual que la anterior, pero para SpO₂. Como el máximo posible es 100 %, los valores se amontonan "
                    "contra ese borde y quedan pocos valores bajos a la izquierda (la 'cola').",
                    f"La mitad central está entre {q1:.1f} % y {q3:.1f} %. El valor más bajo registrado fue "
                    f"{validas['spo2_percent'].min():.1f} %.")

        diario = validas.groupby("fecha").agg(BPM=("heart_rate_bpm", "mean"), SpO2=("spo2_percent", "mean"),
                                              n=("student_id", "size")).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=diario["fecha"], y=diario["BPM"], name="BPM promedio", mode="lines+markers",
                                 line=dict(color=AZUL, width=3), marker=dict(size=8, line=dict(color=NAVY, width=1.5)),
                                 customdata=diario["n"], hovertemplate="%{y:.1f} BPM · %{customdata} mediciones<extra></extra>"))
        fig.add_trace(go.Scatter(x=diario["fecha"], y=diario["SpO2"], name="SpO₂ promedio (%)", mode="lines+markers",
                                 line=dict(color=MOSTAZA, width=3), marker=dict(size=8, line=dict(color=NAVY, width=1.5)),
                                 yaxis="y2", customdata=diario["n"],
                                 hovertemplate="%{y:.2f} % · %{customdata} mediciones<extra></extra>"))
        fig.update_layout(yaxis=dict(title="BPM"), yaxis2=dict(title="SpO₂ (%)", overlaying="y", side="right"),
                          legend=dict(orientation="h", y=1.14))
        tarjeta("Promedio diario de BPM y SpO₂", estilo(fig, 320),
                "Cada punto es el promedio de un día. La línea azul usa el eje izquierdo (BPM) y la mostaza el derecho (SpO₂). "
                "Pasa el cursor sobre un punto para ver cuántas mediciones lo sustentan.",
                f"El promedio diario de BPM se mueve entre {diario['BPM'].min():.1f} y {diario['BPM'].max():.1f}. "
                "Los saltos más grandes suelen coincidir con fines de semana, cuando hay pocas mediciones y el promedio es menos estable.")

        c3, c4 = st.columns(2)
        with c3:
            fig = px.box(validas, x="hora", y="heart_rate_bpm", labels={"hora": "Hora del día", "heart_rate_bpm": "BPM"})
            fig.update_traces(marker_color=AZUL, line_color=NAVY, fillcolor="#BFD2F5")
            med = validas.groupby("hora")["heart_rate_bpm"].median()
            tarjeta("BPM según la hora del día", estilo(fig),
                    "Cada caja resume las mediciones de una hora: la línea del centro es la mediana, la caja contiene a la "
                    "mitad central y los puntos sueltos son valores atípicos.",
                    f"La mediana por hora varía solo entre {med.min():.0f} y {med.max():.0f} BPM: la hora del día casi no "
                    "cambia los valores.")
        with c4:
            b_lo, b_hi = limites_iqr(validas_all["heart_rate_bpm"])
            s_lo, s_hi = limites_iqr(validas_all["spo2_percent"])
            tmp = validas.copy()
            tmp["Tipo"] = (~tmp["heart_rate_bpm"].between(b_lo, b_hi)
                           | ~tmp["spo2_percent"].between(s_lo, s_hi)).map({True: "Atípico", False: "Habitual"})
            fig = px.scatter(tmp, x="heart_rate_bpm", y="spo2_percent", color="Tipo", opacity=0.65,
                             color_discrete_map={"Habitual": AZUL, "Atípico": ROJO},
                             labels={"heart_rate_bpm": "BPM", "spo2_percent": "SpO₂ (%)"},
                             hover_data=["student_id", "timestamp"])
            fig.update_traces(marker=dict(size=8, line=dict(color=NAVY, width=0.8)))
            corr = validas["heart_rate_bpm"].corr(validas["spo2_percent"]) if len(validas) > 2 else float("nan")
            tarjeta("¿Se relacionan BPM y SpO₂?", estilo(fig),
                    f"Cada punto es una medición: a la derecha, más latidos; arriba, más oxígeno. En rojo, los atípicos "
                    f"(fuera de 1.5×IQR del conjunto completo: BPM fuera de [{b_lo:.0f}, {b_hi:.0f}] o SpO₂ fuera de "
                    f"[{s_lo:.1f}, {s_hi:.1f}]). Criterio estadístico, no clínico.",
                    f"{int((tmp['Tipo'] == 'Atípico').sum())} de {len(tmp)} mediciones son atípicas. "
                    f"La nube no sigue ninguna diagonal (correlación {corr:.2f}): un valor no predice el otro.")

# --------------------------------------------------------------------------- #
# 3. Seguimiento individual
# --------------------------------------------------------------------------- #
with tab_ind:
    if estudiante != "Todos":
        sel = estudiante
        st.info(f"Mostrando el estudiante elegido en la barra lateral: **{sel}**.")
    else:
        conteo = base["student_id"].value_counts()
        opciones = sorted(base["student_id"].unique())
        sel = st.selectbox("Elige un estudiante", opciones, index=opciones.index(conteo.index[0]),
                           help="Por defecto, el estudiante con más mediciones en el período filtrado.")

    hist = base[base["student_id"] == sel].sort_values("timestamp")
    h_val = hist[hist["estado_valido"]]
    n_h = len(hist)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Identificador", sel)
    c2.metric("Mediciones registradas", n_h)
    c3.metric("Primera medición", fmt_fecha(hist["timestamp"].min()), hist["timestamp"].min().strftime("%H:%M"),
              delta_color="off", delta_arrow="off")
    c4.metric("Última medición", fmt_fecha(hist["timestamp"].max()), hist["timestamp"].max().strftime("%H:%M"),
              delta_color="off", delta_arrow="off")
    st.write("")

    # ---- Informe en palabras ------------------------------------------------
    g_bpm, g_bpm_sd = validas_all["heart_rate_bpm"].mean(), validas_all["heart_rate_bpm"].std()
    g_spo, g_spo_sd = validas_all["spo2_percent"].mean(), validas_all["spo2_percent"].std()
    med_grupo = df_all.groupby("student_id").size().median()
    dias_dist = hist["fecha"].nunique()

    def comparar(valor: float, ref: float, unidad: str) -> str:
        d = valor - ref
        if abs(d) < 0.05:
            return f"prácticamente igual al promedio del grupo ({ref:.1f}{unidad})"
        return f"{abs(d):.1f}{unidad} {'por encima' if d > 0 else 'por debajo'} del promedio del grupo ({ref:.1f}{unidad})"

    def variacion(s: float, ref: float) -> str:
        if s < ref * 0.75:
            return "varían menos que en el resto del grupo"
        if s > ref * 1.25:
            return "varían más que en el resto del grupo"
        return "varían de forma parecida a las del grupo"

    def evolucion(serie: pd.Series, sd_grupo: float, unidad: str) -> str:
        if len(serie) < 6:
            return "hay muy pocas mediciones para hablar de una tendencia"
        mitad = len(serie) // 2
        a, b = serie.iloc[:mitad].mean(), serie.iloc[mitad:].mean()
        if abs(b - a) < 0.4 * sd_grupo:
            return f"la primera mitad promedió {a:.1f}{unidad} y la segunda {b:.1f}{unidad}: sin cambio claro"
        return (f"la primera mitad promedió {a:.1f}{unidad} y la segunda {b:.1f}{unidad}: "
                f"un poco {'más alto' if b > a else 'más bajo'} con el tiempo")

    items = [f"📅 <b>Uso.</b> {sel} se midió <b>{n_h}</b> veces en <b>{dias_dist}</b> días distintos, entre el "
             f"{fmt_fecha(hist['timestamp'].min())} y el {fmt_fecha(hist['timestamp'].max())}. "
             f"{'Es más' if n_h > med_grupo else 'Es menos' if n_h < med_grupo else 'Es igual'} que la mediana del grupo "
             f"({med_grupo:.0f} mediciones)."]
    horas_rep = hist["hora"].value_counts()
    if n_h >= 4 and horas_rep.iloc[0] >= 2:
        items.append(f"⏰ <b>Hábito.</b> La hora en que más se midió fue las {horas_rep.index[0]}h "
                     f"({horas_rep.iloc[0]} de {n_h} veces).")
    if len(h_val):
        bpm_m, bpm_s = h_val["heart_rate_bpm"].mean(), h_val["heart_rate_bpm"].std()
        spo_m, spo_s = h_val["spo2_percent"].mean(), h_val["spo2_percent"].std()
        items.append(f"❤️ <b>Frecuencia cardíaca.</b> Su promedio fue <b>{bpm_m:.1f} BPM</b>, {comparar(bpm_m, g_bpm, '')}. "
                     f"Sus valores fueron de {h_val['heart_rate_bpm'].min()} a {h_val['heart_rate_bpm'].max()} BPM"
                     + (f" y sus mediciones {variacion(bpm_s, g_bpm_sd)}. " if len(h_val) > 2 else ". ")
                     + f"En el tiempo, {evolucion(h_val['heart_rate_bpm'], g_bpm_sd, '')}.")
        items.append(f"🫁 <b>Oxígeno.</b> Su promedio fue <b>{spo_m:.1f} %</b>, {comparar(spo_m, g_spo, ' %')}. "
                     f"Sus valores fueron de {h_val['spo2_percent'].min():.1f} % a {h_val['spo2_percent'].max():.1f} %. "
                     f"En el tiempo, {evolucion(h_val['spo2_percent'], g_spo_sd, ' %')}.")
    n_inv_h = int((~hist["estado_valido"]).sum())
    items.append(f"🧪 <b>Calidad.</b> {n_inv_h} de sus {n_h} mediciones fueron inválidas"
                 + (" y no se usan en los promedios." if n_inv_h else "."))
    st.markdown('<div class="titulo-g">📝 El informe de este estudiante, en palabras</div>', unsafe_allow_html=True)
    st.markdown('<div class="informe"><ul>' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
                '<p style="font-size:.85rem;opacity:.85">Este resumen describe las mediciones que hizo en el tótem '
                '(datos simulados). No es una evaluación de salud.</p></div>', unsafe_allow_html=True)
    st.write("")

    if n_h < 2:
        st.info("Este estudiante tiene una sola medición en el período: no hay evolución que mostrar.")

    # ---- Gráficas de evolución ---------------------------------------------
    def grafica_evolucion(col: str, g_media: float, g_sd: float, etiqueta: str, color: str, unidad: str):
        fig = go.Figure()
        fig.add_hrect(y0=g_media - g_sd, y1=g_media + g_sd, fillcolor=AMARILLO, opacity=0.28, line_width=0)
        if len(h_val):
            fig.add_trace(go.Scatter(x=h_val["timestamp"], y=h_val[col], mode="lines+markers", name="Medición válida",
                                     line=dict(color=color, width=3),
                                     marker=dict(size=10, color=color, line=dict(color=NAVY, width=1.5))))
            fig.add_hline(y=h_val[col].mean(), line_dash="dot", line_color=NAVY, line_width=2,
                          annotation_text=f"Su promedio {h_val[col].mean():.1f}{unidad}", annotation_position="top left")
            i_max, i_min = h_val[col].idxmax(), h_val[col].idxmin()
            for i, txt in ((i_max, "máx."), (i_min, "mín.")):
                fig.add_annotation(x=h_val.loc[i, "timestamp"], y=h_val.loc[i, col],
                                   text=f"{txt} {h_val.loc[i, col]:.1f}{unidad}", showarrow=True, arrowhead=2,
                                   ay=-30 if txt == "máx." else 30, font=dict(size=12), bgcolor="#fff",
                                   bordercolor=NAVY, borderwidth=1.5)
        h_inv = hist[~hist["estado_valido"]]
        if len(h_inv):
            fig.add_trace(go.Scatter(x=h_inv["timestamp"], y=h_inv[col], mode="markers", name="Medición inválida",
                                     marker=dict(color=ROJO, size=13, symbol="x", line=dict(color=ROJO, width=3))))
        fig.update_layout(yaxis_title=etiqueta, xaxis_title="Fecha de la medición", legend=dict(orientation="h", y=1.14))
        return estilo(fig, 340)

    if len(h_val):
        dentro_b = int(h_val["heart_rate_bpm"].between(g_bpm - g_bpm_sd, g_bpm + g_bpm_sd).sum())
        dentro_s = int(h_val["spo2_percent"].between(g_spo - g_spo_sd, g_spo + g_spo_sd).sum())
        lb = (f"{dentro_b} de {len(h_val)} mediciones válidas cayeron dentro de la franja del grupo. "
              f"La más alta fue de {h_val['heart_rate_bpm'].max()} BPM el {fmt_fecha(h_val.loc[h_val['heart_rate_bpm'].idxmax(), 'timestamp'])}.")
        ls = (f"{dentro_s} de {len(h_val)} mediciones válidas cayeron dentro de la franja del grupo. "
              f"La más baja fue de {h_val['spo2_percent'].min():.1f} % el {fmt_fecha(h_val.loc[h_val['spo2_percent'].idxmin(), 'timestamp'])}.")
    else:
        lb = ls = ""
    como_comun = ("Cada punto es una medición, unidas en orden cronológico. La <b>franja amarilla</b> es la zona donde cae "
                  "la mayoría del grupo (promedio ± 1 desviación estándar); la <b>línea punteada</b> es el promedio de este "
                  "estudiante. Las <b>X rojas</b> son mediciones inválidas. Variar un poco de una medición a otra es normal.")
    tarjeta("Evolución de la frecuencia cardíaca", grafica_evolucion("heart_rate_bpm", g_bpm, g_bpm_sd, "BPM", AZUL, ""),
            como_comun, lb)
    tarjeta("Evolución de la saturación de oxígeno", grafica_evolucion("spo2_percent", g_spo, g_spo_sd, "SpO₂ (%)", VERDE, " %"),
            como_comun + " Como el tope es 100 %, es habitual ver los puntos pegados arriba.", ls)

    c1, c2 = st.columns(2)
    with c1:
        horas = hist.groupby("hora").size().reset_index(name="mediciones")
        fig = px.bar(horas, x="hora", y="mediciones", labels={"hora": "Hora del día", "mediciones": "Mediciones"})
        fig.update_traces(marker_color=MOSTAZA)
        fig.update_xaxes(dtick=1)
        tarjeta("¿A qué horas se mide?", granular(estilo(fig, 280)),
                "Cada barra cuenta cuántas veces se midió en esa hora del día. Sirve para ver si tiene una rutina.")
    with c2:
        dias_s = hist.groupby("dia_semana").size().reindex(range(7), fill_value=0).reset_index(name="mediciones")
        dias_s["Día"] = dias_s["dia_semana"].map(dict(enumerate(DIAS)))
        fig = px.bar(dias_s, x="Día", y="mediciones", labels={"mediciones": "Mediciones"})
        fig.update_traces(marker_color=AZUL)
        tarjeta("¿Qué días de la semana?", granular(estilo(fig, 280)),
                "Cuenta las mediciones por día de la semana. Una barra en cero significa que ese día nunca se midió.")

    with st.expander("Ver la tabla de mediciones del estudiante"):
        st.dataframe(hist[["timestamp", "heart_rate_bpm", "spo2_percent", "signal_quality", "measurement_status"]]
                     .rename(columns={"timestamp": "Fecha y hora", "heart_rate_bpm": "BPM", "spo2_percent": "SpO₂ (%)",
                                      "signal_quality": "Calidad de señal", "measurement_status": "Estado"}),
                     width="stretch", hide_index=True)

# --------------------------------------------------------------------------- #
# 4. Calidad de datos
# --------------------------------------------------------------------------- #
with tab_cal:
    c1, c2 = st.columns(2)
    with c1:
        est = df["measurement_status"].map({"valid": "Válida", "invalid": "Inválida"}).value_counts().reset_index()
        est.columns = ["Estado", "Mediciones"]
        fig = px.pie(est, names="Estado", values="Mediciones", hole=0.55, color="Estado",
                     color_discrete_map={"Válida": AZUL, "Inválida": ROJO})
        fig.update_traces(marker=dict(line=dict(color=NAVY, width=2.5)), textinfo="percent+label")
        tarjeta("Mediciones válidas vs inválidas", estilo(fig, 320),
                "El círculo completo son todas las mediciones; cada color es la parte que el tótem marcó como válida o inválida.",
                f"{pct(n_inval, n_total):.1f} % de las mediciones ({n_inval}) fueron inválidas.")
    with c2:
        inv_h = df.groupby("hora")["estado_valido"].agg(n="size", inv=lambda s: (~s).sum()).reset_index()
        inv_h["pct"] = 100 * inv_h["inv"] / inv_h["n"]
        fig = px.bar(inv_h, x="hora", y="pct", labels={"hora": "Hora del día", "pct": "% inválidas"},
                     hover_data={"n": True, "inv": True})
        fig.update_traces(marker_color=ROJO)
        fig.update_xaxes(dtick=1)
        fiable = inv_h[inv_h["n"] >= 20]
        lect = ""
        if len(fiable):
            r = fiable.loc[fiable["pct"].idxmax()]
            lect = f"La hora con mayor porcentaje fue las {int(r['hora'])}h ({r['pct']:.1f} %, {int(r['inv'])} de {int(r['n'])})."
        tarjeta("¿A qué horas fallan más las mediciones?", granular(estilo(fig, 320)),
                "Cada barra es el porcentaje de mediciones inválidas dentro de esa hora. Ojo: horas con muy pocas "
                "mediciones (como las 21h) dan porcentajes poco confiables.", lect)

    dq = df.assign(Estado=df["measurement_status"].map({"valid": "Válida", "invalid": "Inválida"}))
    fig = px.box(dq, x="Estado", y="signal_quality", color="Estado",
                 color_discrete_map={"Válida": AZUL, "Inválida": ROJO}, labels={"signal_quality": "Calidad de señal (0 a 1)"})
    fig.update_layout(showlegend=False)
    prom = dq.groupby("Estado")["signal_quality"].mean()
    lect = " · ".join(f"{k}: {v:.3f}" for k, v in prom.items())
    tarjeta("¿Las inválidas tienen peor señal?", estilo(fig, 300),
            "Compara la calidad de señal (1 = perfecta) de las mediciones válidas e inválidas. Si las inválidas fueran "
            "por mala señal, su caja estaría mucho más abajo.",
            f"Promedios de calidad de señal → {lect}. Casi idénticos: la etiqueta 'inválida' no se explica por la señal.")

    with st.container(border=True):
        st.markdown('<div class="titulo-g">Chequeos de calidad (conjunto completo, sin filtros)</div>', unsafe_allow_html=True)
        b_lo, b_hi = limites_iqr(validas_all["heart_rate_bpm"])
        s_lo, s_hi = limites_iqr(validas_all["spo2_percent"])
        resumen = pd.DataFrame({
            "Chequeo": ["Valores nulos", "Filas duplicadas", "Mediciones inválidas",
                        f"BPM atípico (fuera de {b_lo:.0f}–{b_hi:.0f}, válidas)",
                        f"SpO₂ atípica (fuera de {s_lo:.1f}–{s_hi:.1f}, válidas)", "Calidad de señal mínima observada"],
            "Resultado": [str(int(df_all.isna().sum().sum())), str(int(df_all.duplicated().sum())),
                          f"{(~df_all['estado_valido']).sum()} ({pct((~df_all['estado_valido']).sum(), len(df_all)):.1f} %)",
                          str(int((~validas_all['heart_rate_bpm'].between(b_lo, b_hi)).sum())),
                          str(int((~validas_all['spo2_percent'].between(s_lo, s_hi)).sum())),
                          f"{df_all['signal_quality'].min():.2f}"]})
        st.dataframe(resumen, hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# 5. Hallazgos (sobre el conjunto completo, para que no cambien con los filtros)
# --------------------------------------------------------------------------- #
with tab_hall:
    st.caption("Los hallazgos se calculan sobre **todo** el conjunto de datos, sin filtros, y cada cifra se recalcula desde el CSV.")
    A, n = df_all, len(df_all)
    V = validas_all

    dias_sem = A[~A["es_fin_de_semana"]]["fecha"].nunique()
    dias_fin = A[A["es_fin_de_semana"]]["fecha"].nunique()
    prom_sem = (~A["es_fin_de_semana"]).sum() / dias_sem
    prom_fin = A["es_fin_de_semana"].sum() / dias_fin
    pct_sem = pct((~A["es_fin_de_semana"]).sum(), n)
    por_hora_all = A.groupby("hora").size()
    h_pico, h_min = por_hora_all.idxmax(), por_hora_all[por_hora_all.index < 21].idxmin()

    por_est_all = A.groupby("student_id").size().sort_values(ascending=False)
    top10 = int(round(len(por_est_all) * 0.10))
    pct_top = pct(por_est_all.head(top10).sum(), n)

    inv = A[~A["estado_valido"]]
    q_v, q_i = A[A["estado_valido"]]["signal_quality"].mean(), inv["signal_quality"].mean()

    b_lo, b_hi = limites_iqr(V["heart_rate_bpm"])
    s_lo, s_hi = limites_iqr(V["spo2_percent"])
    n_b = int((~V["heart_rate_bpm"].between(b_lo, b_hi)).sum())
    n_s = int((~V["spo2_percent"].between(s_lo, s_hi)).sum())
    corr = V["heart_rate_bpm"].corr(V["spo2_percent"])

    hallazgos = [
        ("El tótem se usa casi exclusivamente entre semana",
         f"- {pct_sem:.0f} % de las mediciones ocurre de lunes a viernes: **{prom_sem:.0f} mediciones por día** entre semana frente a **{prom_fin:.0f}** en fin de semana.\n"
         f"- Dentro del día el uso es **muy parejo** entre las 7h y las 20h (la hora más usada es las {h_pico}h con {por_hora_all[h_pico]} mediciones y la menos usada, las {h_min}h con {por_hora_all[h_min]}); no hay una hora pico marcada. A partir de las 21h casi no hay uso."),
        ("El uso por estudiante es moderadamente desigual",
         f"- {A['student_id'].nunique()} estudiantes distintos; mediana de **{por_est_all.median():.0f} mediciones por estudiante** (máximo {por_est_all.max()}, mínimo {por_est_all.min()}).\n"
         f"- El 10 % más activo ({top10} estudiantes) genera {pct_top:.0f} % de las mediciones; {int((por_est_all == 1).sum())} estudiantes solo se midieron una vez."),
        (f"{pct(len(inv), n):.1f} % de mediciones inválidas, sin relación aparente con la señal",
         f"- Hay {len(inv)} mediciones inválidas de {n:,}. Su `signal_quality` promedio ({q_i:.3f}) es casi igual al de las válidas ({q_v:.3f}) y toda la señal está entre {A['signal_quality'].min():.2f} y {A['signal_quality'].max():.2f}.\n"
         "- La etiqueta `invalid` **no se puede explicar** con la calidad de señal: conviene documentar el criterio con quien administra el dispositivo."),
        ("BPM y SpO₂ son estables, con pocos atípicos y sin relación entre sí",
         f"- BPM: promedio {V['heart_rate_bpm'].mean():.1f} (desv. {V['heart_rate_bpm'].std():.1f}), rango {V['heart_rate_bpm'].min()}–{V['heart_rate_bpm'].max()}; {n_b} mediciones fuera de [{b_lo:.0f}, {b_hi:.0f}].\n"
         f"- SpO₂: promedio {V['spo2_percent'].mean():.1f} %, rango {V['spo2_percent'].min():.1f}–{V['spo2_percent'].max():.1f}; {n_s} mediciones por debajo de {s_lo:.1f} %. La distribución está pegada al 100 %, con cola hacia valores bajos.\n"
         f"- La correlación entre BPM y SpO₂ es {corr:.2f}, es decir, prácticamente nula."),
    ]
    c1, c2 = st.columns(2)
    for i, (titulo, texto) in enumerate(hallazgos):
        with (c1 if i % 2 == 0 else c2).container(border=True):
            st.markdown(f'<span class="hallazgo-n">{i + 1}</span><span class="titulo-g">{titulo}</span>', unsafe_allow_html=True)
            st.markdown(texto)

    with st.container(border=True):
        st.markdown('<div class="titulo-g">⚠️ Limitaciones</div>', unsafe_allow_html=True)
        st.markdown(
            "- Los datos son **sintéticos**: los patrones reflejan cómo se generó el archivo, no el comportamiento de estudiantes reales.\n"
            "- El MAX30102 de este escenario es educativo y **no es un dispositivo médico validado**; BPM y SpO₂ aislados no permiten "
            "evaluar la salud de nadie. Los atípicos aquí son estadísticos, no diagnósticos.\n"
            "- La muestra es voluntaria y de una sola estación (`IOT-STATION-001`): no representa a toda la población universitaria.\n"
            "- El criterio de `invalid` no está documentado y no coincide con `signal_quality`.\n"
            "- El primer día (29/09) y el último (28/10) están incompletos en hora de Colombia."
        )
