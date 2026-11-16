"""Dashboard del tótem IoT de monitoreo fisiológico (EAFIT) - datos sintéticos.

Ejecutar localmente:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

CSV_PATH = Path(__file__).parent / "proyecto_integrador_eafit_max30102.csv"
TZ = "America/Bogota"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
COLOR = "#1F4E79"      # color principal
COLOR_2 = "#E07B39"    # color de contraste (inválidas / atípicos / fines de semana)
ESTADOS = {"Todas": None, "Solo válidas": "valid", "Solo inválidas": "invalid"}

st.set_page_config(page_title="Tótem IoT EAFIT", page_icon="🫀", layout="wide")


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


df_all = cargar_datos()
validas_all = df_all[df_all["estado_valido"]]

# --------------------------------------------------------------------------- #
# Filtros (barra lateral)
# --------------------------------------------------------------------------- #
st.sidebar.header("Filtros")
f_min, f_max = df_all["fecha"].min().date(), df_all["fecha"].max().date()

rango = st.sidebar.date_input(
    "Rango de fechas", value=(f_min, f_max), min_value=f_min, max_value=f_max
)
# Mientras el usuario elige la fecha final, date_input devuelve una sola fecha
f_ini, f_fin = (rango[0], rango[1]) if len(rango) == 2 else (rango[0], rango[0])

estudiantes = ["Todos"] + sorted(df_all["student_id"].unique())
estudiante = st.sidebar.selectbox("Estudiante", estudiantes)

estado_label = st.sidebar.radio("Estado de la medición", list(ESTADOS), horizontal=False)
estado = ESTADOS[estado_label]

# Base con fecha + estado (sin estudiante): se usa en la pestaña de seguimiento individual
base = df_all[(df_all["fecha"].dt.date >= f_ini) & (df_all["fecha"].dt.date <= f_fin)]
if estado:
    base = base[base["measurement_status"] == estado]
df = base if estudiante == "Todos" else base[base["student_id"] == estudiante]

st.sidebar.caption(
    f"{len(df):,} de {len(df_all):,} mediciones con los filtros actuales.\n\n"
    "Datos **sintéticos**; las horas se muestran en hora de Colombia (UTC-5)."
)

# --------------------------------------------------------------------------- #
# Encabezado e indicadores
# --------------------------------------------------------------------------- #
st.title("🫀 Tótem IoT de monitoreo fisiológico · EAFIT")
st.caption(
    "Análisis de mediciones de frecuencia cardíaca (BPM) y saturación de oxígeno (SpO₂) "
    "del sensor MAX30102. Datos simulados, sin valor clínico."
)

if df.empty:
    st.warning("No hay mediciones con los filtros seleccionados. Amplía el rango de fechas o cambia el estado.")
    st.stop()

validas = df[df["estado_valido"]]
n_total = len(df)
n_inval = int((~df["estado_valido"]).sum())

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Mediciones", f"{n_total:,}")
k2.metric("Estudiantes distintos", f"{df['student_id'].nunique():,}")
k3.metric("BPM promedio (válidas)", f"{validas['heart_rate_bpm'].mean():.1f}" if len(validas) else "—")
k4.metric("SpO₂ promedio (válidas)", f"{validas['spo2_percent'].mean():.1f} %" if len(validas) else "—")
k5.metric("Mediciones inválidas", f"{n_inval:,}", f"{pct(n_inval, n_total):.1f} % del total", delta_color="off")

tab_uso, tab_fisio, tab_ind, tab_cal, tab_hall = st.tabs(
    ["📈 Uso del tótem", "❤️ Indicadores fisiológicos", "👤 Seguimiento individual",
     "🧪 Calidad de datos", "💡 Hallazgos"]
)

# --------------------------------------------------------------------------- #
# 1. Uso del tótem
# --------------------------------------------------------------------------- #
with tab_uso:
    st.subheader("Mediciones por día")
    por_dia = df.groupby("fecha").agg(
        mediciones=("student_id", "size"), fin_de_semana=("es_fin_de_semana", "first")
    ).reset_index()
    por_dia["Tipo de día"] = por_dia["fin_de_semana"].map({True: "Fin de semana", False: "Entre semana"})
    fig = px.bar(
        por_dia, x="fecha", y="mediciones", color="Tipo de día",
        color_discrete_map={"Entre semana": COLOR, "Fin de semana": COLOR_2},
        labels={"fecha": "Fecha", "mediciones": "Mediciones"},
    )
    fig.update_layout(legend_title_text="", margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Horarios de mayor uso")
        por_hora = df.groupby("hora").size().reindex(range(24), fill_value=0).reset_index(name="mediciones")
        por_hora = por_hora[por_hora["mediciones"] > 0]
        fig = px.bar(por_hora, x="hora", y="mediciones",
                     labels={"hora": "Hora del día (Colombia)", "mediciones": "Mediciones"})
        fig.update_traces(marker_color=COLOR)
        fig.update_xaxes(dtick=1)
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("Día de la semana × hora")
        mapa = df.pivot_table(index="dia_semana", columns="hora", values="student_id",
                              aggfunc="size", fill_value=0).reindex(range(7), fill_value=0)
        fig = px.imshow(
            mapa.values, x=[f"{h}h" for h in mapa.columns], y=DIAS, aspect="auto",
            color_continuous_scale="Blues", labels=dict(color="Mediciones"),
        )
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    st.subheader("¿Qué tan frecuente es el uso por estudiante?")
    por_est = df.groupby("student_id").size().rename("mediciones").reset_index()
    c3, c4 = st.columns(2)
    with c3:
        fig = px.histogram(por_est, x="mediciones", nbins=20,
                           labels={"mediciones": "Mediciones por estudiante"})
        fig.update_traces(marker_color=COLOR)
        fig.update_layout(yaxis_title="Número de estudiantes", margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
    with c4:
        top = por_est.nlargest(15, "mediciones").sort_values("mediciones")
        fig = px.bar(top, x="mediciones", y="student_id", orientation="h",
                     labels={"mediciones": "Mediciones", "student_id": ""}, title="Top 15 estudiantes")
        fig.update_traces(marker_color=COLOR)
        fig.update_layout(margin=dict(t=40))
        st.plotly_chart(fig, width="stretch")

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
            st.subheader("Distribución de frecuencia cardíaca")
            fig = px.histogram(validas, x="heart_rate_bpm", nbins=40,
                               labels={"heart_rate_bpm": "BPM"})
            fig.update_traces(marker_color=COLOR)
            fig.add_vline(x=validas["heart_rate_bpm"].mean(), line_dash="dash", line_color=COLOR_2,
                          annotation_text=f"Promedio {validas['heart_rate_bpm'].mean():.1f}")
            fig.update_layout(yaxis_title="Mediciones", margin=dict(t=10))
            st.plotly_chart(fig, width="stretch")
        with c2:
            st.subheader("Distribución de saturación de oxígeno")
            fig = px.histogram(validas, x="spo2_percent", nbins=40, labels={"spo2_percent": "SpO₂ (%)"})
            fig.update_traces(marker_color=COLOR)
            fig.add_vline(x=validas["spo2_percent"].mean(), line_dash="dash", line_color=COLOR_2,
                          annotation_text=f"Promedio {validas['spo2_percent'].mean():.1f}")
            fig.update_layout(yaxis_title="Mediciones", margin=dict(t=10))
            st.plotly_chart(fig, width="stretch")

        st.subheader("Evolución diaria del promedio")
        diario = validas.groupby("fecha").agg(
            BPM=("heart_rate_bpm", "mean"), SpO2=("spo2_percent", "mean"), n=("student_id", "size")
        ).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=diario["fecha"], y=diario["BPM"], name="BPM promedio",
                                 mode="lines+markers", line=dict(color=COLOR)))
        fig.add_trace(go.Scatter(x=diario["fecha"], y=diario["SpO2"], name="SpO₂ promedio (%)",
                                 mode="lines+markers", line=dict(color=COLOR_2), yaxis="y2"))
        fig.update_layout(
            yaxis=dict(title="BPM"), yaxis2=dict(title="SpO₂ (%)", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.12), margin=dict(t=10),
        )
        st.plotly_chart(fig, width="stretch")
        st.caption("Los días con pocas mediciones (fines de semana) tienen promedios más variables.")

        c3, c4 = st.columns(2)
        with c3:
            st.subheader("BPM por hora del día")
            fig = px.box(validas, x="hora", y="heart_rate_bpm",
                         labels={"hora": "Hora (Colombia)", "heart_rate_bpm": "BPM"})
            fig.update_traces(marker_color=COLOR, line_color=COLOR)
            fig.update_layout(margin=dict(t=10))
            st.plotly_chart(fig, width="stretch")
        with c4:
            st.subheader("BPM vs SpO₂ (atípicos resaltados)")
            b_lo, b_hi = limites_iqr(validas_all["heart_rate_bpm"])
            s_lo, s_hi = limites_iqr(validas_all["spo2_percent"])
            tmp = validas.copy()
            tmp["Atípico"] = (~tmp["heart_rate_bpm"].between(b_lo, b_hi)
                              | ~tmp["spo2_percent"].between(s_lo, s_hi)).map({True: "Atípico", False: "Normal"})
            fig = px.scatter(tmp, x="heart_rate_bpm", y="spo2_percent", color="Atípico", opacity=0.6,
                             color_discrete_map={"Normal": COLOR, "Atípico": COLOR_2},
                             labels={"heart_rate_bpm": "BPM", "spo2_percent": "SpO₂ (%)"},
                             hover_data=["student_id", "timestamp"])
            fig.update_layout(legend_title_text="", margin=dict(t=10))
            st.plotly_chart(fig, width="stretch")
            st.caption(
                f"Atípico = fuera de 1.5×IQR del conjunto completo de mediciones válidas "
                f"(BPM fuera de [{b_lo:.0f}, {b_hi:.0f}] o SpO₂ fuera de [{s_lo:.1f}, {s_hi:.1f}]). "
                "Es un criterio estadístico, **no clínico**."
            )

# --------------------------------------------------------------------------- #
# 3. Seguimiento individual
# --------------------------------------------------------------------------- #
with tab_ind:
    if estudiante != "Todos":
        sel = estudiante
        st.info(f"Mostrando el estudiante seleccionado en la barra lateral: **{sel}**.")
    else:
        conteo = base["student_id"].value_counts()
        opciones = sorted(base["student_id"].unique())
        if not opciones:
            st.info("No hay estudiantes con los filtros actuales.")
            st.stop()
        sel = st.selectbox("Selecciona un estudiante", opciones,
                           index=opciones.index(conteo.index[0]),
                           help="Por defecto, el estudiante con más mediciones en el período filtrado.")

    hist = base[base["student_id"] == sel].sort_values("timestamp")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Identificador", sel)
    c2.metric("Mediciones registradas", len(hist))
    c3.metric("Primera medición", hist["timestamp"].min().strftime("%d/%m/%Y %H:%M"))
    c4.metric("Última medición", hist["timestamp"].max().strftime("%d/%m/%Y %H:%M"))

    h_val = hist[hist["estado_valido"]]
    if len(hist) < 2:
        st.info("Este estudiante tiene una sola medición en el período: no hay evolución que mostrar.")
    for col, titulo, etiqueta in [("heart_rate_bpm", "Evolución de la frecuencia cardíaca", "BPM"),
                                  ("spo2_percent", "Evolución de la saturación de oxígeno", "SpO₂ (%)")]:
        st.subheader(titulo)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=h_val["timestamp"], y=h_val[col], mode="lines+markers",
                                 name="Válida", line=dict(color=COLOR)))
        h_inv = hist[~hist["estado_valido"]]
        if len(h_inv):
            fig.add_trace(go.Scatter(x=h_inv["timestamp"], y=h_inv[col], mode="markers", name="Inválida",
                                     marker=dict(color=COLOR_2, size=11, symbol="x")))
        if len(h_val):
            fig.add_hline(y=h_val[col].mean(), line_dash="dot", line_color="gray",
                          annotation_text=f"Promedio personal {h_val[col].mean():.1f}")
        fig.update_layout(yaxis_title=etiqueta, xaxis_title="Fecha y hora (Colombia)",
                          legend=dict(orientation="h", y=1.12), margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    with st.expander("Ver tabla de mediciones del estudiante"):
        st.dataframe(
            hist[["timestamp", "heart_rate_bpm", "spo2_percent", "signal_quality", "measurement_status"]],
            width="stretch", hide_index=True,
        )

# --------------------------------------------------------------------------- #
# 4. Calidad de datos
# --------------------------------------------------------------------------- #
with tab_cal:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Válidas vs inválidas")
        est = df["measurement_status"].map({"valid": "Válida", "invalid": "Inválida"}).value_counts().reset_index()
        est.columns = ["Estado", "Mediciones"]
        fig = px.pie(est, names="Estado", values="Mediciones", hole=0.55, color="Estado",
                     color_discrete_map={"Válida": COLOR, "Inválida": COLOR_2})
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("% de inválidas por hora")
        inv_h = df.groupby("hora")["estado_valido"].agg(
            n="size", inv=lambda s: (~s).sum()).reset_index()
        inv_h["pct"] = 100 * inv_h["inv"] / inv_h["n"]
        fig = px.bar(inv_h, x="hora", y="pct", labels={"hora": "Hora (Colombia)", "pct": "% inválidas"},
                     hover_data={"n": True, "inv": True})
        fig.update_traces(marker_color=COLOR_2)
        fig.update_xaxes(dtick=1)
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
        st.caption("Horas con pocas mediciones (p. ej. 21h) dan porcentajes poco estables.")

    st.subheader("Calidad de señal según el estado")
    fig = px.box(df.assign(Estado=df["measurement_status"].map({"valid": "Válida", "invalid": "Inválida"})),
                 x="Estado", y="signal_quality", color="Estado",
                 color_discrete_map={"Válida": COLOR, "Inválida": COLOR_2},
                 labels={"signal_quality": "signal_quality (0–1)"})
    fig.update_layout(showlegend=False, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Resumen de calidad (conjunto completo, sin filtros)")
    b_lo, b_hi = limites_iqr(validas_all["heart_rate_bpm"])
    s_lo, s_hi = limites_iqr(validas_all["spo2_percent"])
    resumen = pd.DataFrame({
        "Chequeo": [
            "Valores nulos", "Filas duplicadas", "Mediciones inválidas",
            f"BPM atípico (fuera de {b_lo:.0f}–{b_hi:.0f}, válidas)",
            f"SpO₂ atípica (fuera de {s_lo:.1f}–{s_hi:.1f}, válidas)",
            "signal_quality mínima observada",
        ],
        "Resultado": [
            str(int(df_all.isna().sum().sum())), str(int(df_all.duplicated().sum())),
            f"{(~df_all['estado_valido']).sum()} ({pct((~df_all['estado_valido']).sum(), len(df_all)):.1f} %)",
            str(int((~validas_all["heart_rate_bpm"].between(b_lo, b_hi)).sum())),
            str(int((~validas_all["spo2_percent"].between(s_lo, s_hi)).sum())),
            f"{df_all['signal_quality'].min():.2f}",
        ],
    })
    st.dataframe(resumen, hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# 5. Hallazgos (calculados sobre el conjunto completo, para que no cambien con los filtros)
# --------------------------------------------------------------------------- #
with tab_hall:
    st.caption("Los hallazgos se calculan sobre **todo** el conjunto de datos, sin filtros, "
               "y cada cifra se recalcula desde el CSV.")
    A = df_all
    n = len(A)

    # H1: uso entre semana vs fin de semana
    dias_sem = A[~A["es_fin_de_semana"]]["fecha"].nunique()
    dias_fin = A[A["es_fin_de_semana"]]["fecha"].nunique()
    prom_sem = (~A["es_fin_de_semana"]).sum() / dias_sem
    prom_fin = A["es_fin_de_semana"].sum() / dias_fin
    pct_sem = pct((~A["es_fin_de_semana"]).sum(), n)
    por_hora_all = A.groupby("hora").size()
    h_pico, h_min = por_hora_all.idxmax(), por_hora_all[por_hora_all.index < 21].idxmin()

    # H2: concentración por estudiante
    por_est_all = A.groupby("student_id").size().sort_values(ascending=False)
    top10 = int(round(len(por_est_all) * 0.10))
    pct_top = pct(por_est_all.head(top10).sum(), n)

    # H3: calidad
    inv = A[~A["estado_valido"]]
    q_v, q_i = A[A["estado_valido"]]["signal_quality"].mean(), inv["signal_quality"].mean()

    # H4: BPM / SpO2
    V = validas_all
    b_lo, b_hi = limites_iqr(V["heart_rate_bpm"])
    s_lo, s_hi = limites_iqr(V["spo2_percent"])
    n_b = int((~V["heart_rate_bpm"].between(b_lo, b_hi)).sum())
    n_s = int((~V["spo2_percent"].between(s_lo, s_hi)).sum())
    corr = V["heart_rate_bpm"].corr(V["spo2_percent"])

    st.markdown(f"""
### 1. El tótem se usa casi exclusivamente entre semana
- {pct_sem:.0f} % de las mediciones ocurre de lunes a viernes: **{prom_sem:.0f} mediciones por día** entre semana frente a **{prom_fin:.0f}** en fin de semana.
- Dentro del día el uso es **muy parejo** entre las 7h y las 20h (la hora más usada es las {h_pico}h con {por_hora_all[h_pico]} mediciones y la menos usada, las {h_min}h con {por_hora_all[h_min]}); no hay una hora pico marcada. A partir de las 21h casi no hay uso.

### 2. El uso por estudiante es moderadamente desigual: el 10 % más activo hace cerca de una quinta parte de las mediciones
- {A['student_id'].nunique()} estudiantes distintos; mediana de **{por_est_all.median():.0f} mediciones por estudiante** (máximo {por_est_all.max()}, mínimo {por_est_all.min()}).
- El 10 % más activo ({top10} estudiantes) genera {pct_top:.0f} % de las mediciones; {int((por_est_all == 1).sum())} estudiantes solo se midieron una vez.

### 3. Calidad de los datos: {pct(len(inv), n):.1f} % de mediciones inválidas, sin relación aparente con la señal
- Hay {len(inv)} mediciones inválidas de {n:,}. Su `signal_quality` promedio ({q_i:.3f}) es casi igual al de las válidas ({q_v:.3f}) y toda la señal está entre {A['signal_quality'].min():.2f} y {A['signal_quality'].max():.2f}.
- Es decir, la etiqueta `invalid` **no se puede explicar** con la calidad de señal: conviene documentar el criterio con quien administra el dispositivo.

### 4. BPM y SpO₂ son estables, con pocos valores atípicos y sin relación entre sí
- BPM: promedio {V['heart_rate_bpm'].mean():.1f} (desv. {V['heart_rate_bpm'].std():.1f}), rango {V['heart_rate_bpm'].min()}–{V['heart_rate_bpm'].max()}; {n_b} mediciones fuera de [{b_lo:.0f}, {b_hi:.0f}].
- SpO₂: promedio {V['spo2_percent'].mean():.1f} %, rango {V['spo2_percent'].min():.1f}–{V['spo2_percent'].max():.1f}; {n_s} mediciones por debajo de {s_lo:.1f} %. La distribución está muy pegada al 100 %, con cola hacia valores bajos.
- La correlación entre BPM y SpO₂ es {corr:.2f}, es decir, prácticamente nula.
""")

    st.markdown("### Limitaciones")
    st.warning(
        "- Los datos son **sintéticos**: los patrones reflejan cómo se generó el archivo, no el comportamiento de estudiantes reales.\n"
        "- El MAX30102 de este escenario es educativo, **no es un dispositivo médico validado**; BPM y SpO₂ aislados no permiten "
        "evaluar la salud de nadie. Los atípicos aquí son estadísticos, no diagnósticos.\n"
        "- La muestra es voluntaria y de una sola estación (`IOT-STATION-001`): no representa a toda la población universitaria.\n"
        "- El criterio de `invalid` no está documentado y no coincide con `signal_quality`.\n"
        "- El primer día (29/09) y el último (28/10) están incompletos en hora de Colombia."
    )
