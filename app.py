import base64
import io
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

CARPETA = Path(__file__).resolve().parent
# Usa el primer logo que exista (SVG o PNG)
ARCHIVO_LOGO = next((CARPETA / n for n in ("logo_copec.svg", "logo_copec.png") if (CARPETA / n).exists()),
                    CARPETA / "logo_copec.svg")

AZUL_COPEC = "#0B3C8C"
ROJO_COPEC = "#E30613"
COLOR_OTRAS = "#95a5a6"
COLORES_BANDERA = {"COPEC": "#1f77b4", "SHELL": "#f1c40f", "ARAMCO": "#2ecc71", "PETROBRAS": "#2ecc71"}

st.set_page_config(page_title="Monitor de Precios - Copec", page_icon="⛽", layout="wide")

# --- ESTILOS ---
st.markdown(f"""
<style>
    .block-container {{ padding-top: 2.2rem; padding-bottom: 4rem; }}

    .encabezado {{
        display: flex; flex-wrap: wrap; align-items: center; gap: 1rem 1.4rem;
        padding: 1.1rem 1.5rem; margin-bottom: 1.2rem; border-radius: 14px;
        background: linear-gradient(100deg, {AZUL_COPEC} 0%, #07285f 100%);
        border-bottom: 4px solid {ROJO_COPEC};
    }}
    .encabezado .logo {{ height: 54px; background: #fff; padding: 6px 12px; border-radius: 10px; }}
    .encabezado .logo-texto {{
        background: #fff; color: {AZUL_COPEC}; font-weight: 900; font-size: 1.6rem;
        letter-spacing: .08em; padding: .3rem .9rem; border-radius: 10px; font-style: italic;
    }}
    .encabezado .titulo {{ color: #fff; font-size: 1.75rem; font-weight: 700; line-height: 1.2; }}
    .encabezado .subtitulo {{ color: #c9d5ec; font-size: .95rem; }}
    .encabezado .actualizacion {{
        margin-left: auto; color: #fff; font-size: .85rem; white-space: nowrap;
        background: rgba(255,255,255,.14); padding: .45rem .9rem; border-radius: 999px;
    }}

    /* Etiquetas de estaciones con el color de su bandera */
    section[data-testid="stSidebar"] span[data-baseweb="tag"][role="button"] {{ background-color: {COLOR_OTRAS} !important; color: #fff !important; }}
    section[data-testid="stSidebar"] span[data-baseweb="tag"][role="button"][aria-label*="(COPEC)"] {{ background-color: #1f77b4 !important; }}
    section[data-testid="stSidebar"] span[data-baseweb="tag"][role="button"][aria-label*="(SHELL)"] {{ background-color: #f1c40f !important; color: #000 !important; }}
    section[data-testid="stSidebar"] span[data-baseweb="tag"][role="button"][aria-label*="(SHELL)"] svg {{ fill: #000 !important; }}
    section[data-testid="stSidebar"] span[data-baseweb="tag"][role="button"][aria-label*="ARAMCO"],
    section[data-testid="stSidebar"] span[data-baseweb="tag"][role="button"][aria-label*="PETROBRAS" i] {{ background-color: #2ecc71 !important; }}

    div[data-testid="stMetric"] {{
        background: rgba(128,128,128,.08); border: 1px solid rgba(128,128,128,.22);
        border-left: 4px solid {ROJO_COPEC}; border-radius: 12px; padding: .75rem 1rem;
    }}

    .pie {{
        position: fixed; right: 0; bottom: 0; z-index: 1000;
        padding: .35rem 1rem; font-size: .75rem; opacity: .8;
        background: rgba(128,128,128,.12); backdrop-filter: blur(6px);
        border-top-left-radius: 10px;
    }}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def cargar_datos_locales():
    df = pd.read_parquet(CARPETA / "datos_precios.parquet")
    try:
        with open(CARPETA / "info_actualizacion.json", "r") as f:
            hora_act = json.load(f).get("hora", "Desconocida")
    except Exception:
        hora_act = "Desconocida"
    return df, hora_act


@st.cache_data(ttl=3600)
def estaciones_por_producto(producto):
    df, _ = cargar_datos_locales()
    est = df.loc[df['Producto'] == producto, ['MAE_Display', 'Bandera']].drop_duplicates()
    est['MAE_Display'] = est['MAE_Display'].astype(str)
    est['Bandera'] = est['Bandera'].astype(str)
    return est.sort_values('MAE_Display')


def color_bandera(texto):
    texto = str(texto).upper()
    for bandera, color in COLORES_BANDERA.items():
        if bandera in texto:
            return color
    return COLOR_OTRAS


def pesos(valor):
    return f"${valor:,.0f}".replace(",", ".")


def encabezado(hora):
    if ARCHIVO_LOGO.exists():
        logo_b64 = base64.b64encode(ARCHIVO_LOGO.read_bytes()).decode()
        tipo = "image/svg+xml" if ARCHIVO_LOGO.suffix == ".svg" else "image/png"
        logo = f'<img class="logo" src="data:{tipo};base64,{logo_b64}" alt="Copec">'
    else:
        logo = '<span class="logo-texto">COPEC</span>'
    st.markdown(f"""
    <div class="encabezado">
        {logo}
        <div>
            <div class="titulo">Monitor Dinámico de Precios de Combustible</div>
            <div class="subtitulo">Evolución de precios por estación de servicio · Chile</div>
        </div>
        <div class="actualizacion">🕒 Actualizado: <b>{hora}</b></div>
    </div>
    """, unsafe_allow_html=True)


def pie_de_pagina():
    st.markdown(
        f'<div class="pie">© {date.today().year} Equipo de Inversiones · Copec — Todos los derechos reservados</div>',
        unsafe_allow_html=True,
    )


try:
    df_raw, hora_actualizacion = cargar_datos_locales()
except Exception as e:
    st.error(f"Error al leer los datos: {e}. Asegúrate de haber subido 'datos_precios.parquet'.")
    df_raw, hora_actualizacion = pd.DataFrame(columns=['MAE_Display', 'Bandera', 'Producto', 'Precio', 'Fecha']), "Desconocida"

if ARCHIVO_LOGO.exists():
    st.logo(str(ARCHIVO_LOGO))
encabezado(hora_actualizacion)
pie_de_pagina()

if df_raw.empty:
    st.stop()

fecha_min = df_raw['Fecha'].min().date()
fecha_max = df_raw['Fecha'].max().date()

# --- ESTADO INICIAL ---
if "f_inicio" not in st.session_state:
    st.session_state.f_inicio = fecha_min
    st.session_state.f_fin = fecha_max
    st.session_state.periodo = "Todo"

PERIODOS_DIAS = {"1M": 30, "3M": 91, "6M": 182, "1A": 365, "3A": 1095}


def aplicar_periodo():
    periodo = st.session_state.periodo
    if periodo is None:
        return
    if periodo == "Todo":
        inicio = fecha_min
    elif periodo == "YTD":
        inicio = date(fecha_max.year, 1, 1)
    else:
        inicio = fecha_max - timedelta(days=PERIODOS_DIAS[periodo])
    st.session_state.f_inicio = max(inicio, fecha_min)
    st.session_state.f_fin = fecha_max


def fecha_manual():
    st.session_state.periodo = None


# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros del Panel")

productos_disponibles = sorted(df_raw['Producto'].dropna().unique())
producto_sel = st.sidebar.selectbox("Selecciona Producto", productos_disponibles)

estaciones = estaciones_por_producto(producto_sel)
banderas_sel = st.sidebar.multiselect(
    "Filtrar por bandera", sorted(estaciones['Bandera'].unique()),
    placeholder="Todas las banderas", help="Limita la lista de estaciones a las banderas elegidas.",
)
if banderas_sel:
    estaciones = estaciones[estaciones['Bandera'].isin(banderas_sel)]
maes_disponibles = estaciones['MAE_Display'].tolist()

# Conserva la selección de estaciones al cambiar de producto o bandera
previas = [m for m in st.session_state.get("maes", []) if m in maes_disponibles]
if not previas and st.session_state.get("producto_previo") != producto_sel:
    previas = maes_disponibles[:3]
st.session_state.maes = previas
st.session_state.producto_previo = producto_sel

maes_sel = st.sidebar.multiselect(
    f"Selecciona Estaciones ({len(maes_disponibles)} con {producto_sel})",
    options=maes_disponibles, key="maes", placeholder="Busca por código MAE o bandera",
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Rango de Fechas**")
st.sidebar.segmented_control(
    "Período rápido", ["1M", "3M", "6M", "1A", "3A", "YTD", "Todo"],
    key="periodo", on_change=aplicar_periodo, label_visibility="collapsed",
)
f_inicio = st.sidebar.date_input("Desde:", min_value=fecha_min, max_value=fecha_max, key="f_inicio", on_change=fecha_manual)
f_fin = st.sidebar.date_input("Hasta:", min_value=fecha_min, max_value=fecha_max, key="f_fin", on_change=fecha_manual)

st.sidebar.markdown("---")
st.sidebar.markdown("**Opciones del gráfico**")
colorear_por = st.sidebar.radio("Colorear líneas por", ["Bandera", "Estación"], horizontal=True)
linea_escalonada = st.sidebar.toggle("Línea escalonada", value=True, help="Muestra el precio vigente hasta el siguiente cambio.")
mostrar_promedio = st.sidebar.toggle("Mostrar promedio de las estaciones", value=False)
mostrar_marcadores = st.sidebar.toggle("Marcar cada cambio de precio", value=False)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Recargar datos", width="stretch"):
    st.cache_data.clear()
    st.rerun()

# --- FILTRADO ---
if f_inicio > f_fin:
    st.sidebar.error("La fecha 'Desde' debe ser anterior a 'Hasta'.")
    df_filtrado = pd.DataFrame()
else:
    df_filtrado = df_raw[(df_raw['Producto'] == producto_sel) & (df_raw['MAE_Display'].isin(maes_sel))]
    df_filtrado = df_filtrado[
        (df_filtrado['Fecha'] >= pd.Timestamp(f_inicio)) &
        (df_filtrado['Fecha'] < pd.Timestamp(f_fin) + pd.Timedelta(days=1))
    ].sort_values('Fecha').copy()
    df_filtrado['MAE_Display'] = df_filtrado['MAE_Display'].astype(str)

if df_filtrado.empty:
    if not maes_sel:
        st.warning("Selecciona al menos un código MAE en la barra lateral.")
    else:
        st.warning(f"No hay precios de **{producto_sel}** para las estaciones seleccionadas en ese rango de fechas.")
    st.stop()

# --- INDICADORES ---
resumen = df_filtrado.groupby('MAE_Display')['Precio'].agg(inicial='first', actual='last', minimo='min', maximo='max')
resumen['variacion'] = (resumen['actual'] / resumen['inicial'] - 1) * 100

mas_barata = resumen['actual'].idxmin()
mas_cara = resumen['actual'].idxmax()
promedio_actual = resumen['actual'].mean()
promedio_inicial = resumen['inicial'].mean()

promedio_diario = df_filtrado.pivot_table(index=df_filtrado['Fecha'].dt.date, columns='MAE_Display',
                                          values='Precio', aggfunc='last').ffill().mean(axis=1)

variacion_promedio = (promedio_actual / promedio_inicial - 1) * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Precio actual promedio", pesos(promedio_actual),
    delta=f"{variacion_promedio:+.1f}% en el período" if round(variacion_promedio, 1) else "Sin variación en el período",
    delta_color="inverse" if round(variacion_promedio, 1) else "off",
    delta_arrow="auto" if round(variacion_promedio, 1) else "off",
    chart_data=promedio_diario.tolist()[-120:], chart_type="area",
)
k2.metric("Estación más barata", pesos(resumen.loc[mas_barata, 'actual']),
          delta=mas_barata, delta_color="off", delta_arrow="off")
k3.metric("Estación más cara", pesos(resumen.loc[mas_cara, 'actual']),
          delta=mas_cara, delta_color="off", delta_arrow="off")
k4.metric(
    "Brecha actual (máx − mín)", pesos(resumen['actual'].max() - resumen['actual'].min()),
    delta=f"{len(resumen)} estaciones comparadas", delta_color="off", delta_arrow="off",
)

# --- PROCESAMIENTO MULTI-ESTACIÓN PARA EXCEL ---
df_excel = df_filtrado.copy()
df_excel['Fecha_Dia'] = df_excel['Fecha'].dt.strftime('%Y-%m-%d')

df_cruzado = df_excel.pivot_table(
    index='Fecha_Dia',
    columns='MAE_Display',
    values='Precio',
    aggfunc='last'
).ffill()

columnas_estaciones = list(df_cruzado.columns)

if len(columnas_estaciones) == 2:
    est1, est2 = columnas_estaciones[0], columnas_estaciones[1]
    df_cruzado['Diferencia ($)'] = df_cruzado[est1] - df_cruzado[est2]
    df_cruzado['Desviación (%)'] = ((df_cruzado[est1] - df_cruzado[est2]) / df_cruzado[est2]) * 100
elif len(columnas_estaciones) > 2:
    df_cruzado['Precio Promedio ($)'] = df_cruzado[columnas_estaciones].mean(axis=1).round(1)
    df_cruzado['Precio Mínimo ($)'] = df_cruzado[columnas_estaciones].min(axis=1)
    df_cruzado['Precio Máximo ($)'] = df_cruzado[columnas_estaciones].max(axis=1)
    df_cruzado['Dispersión / Brecha ($)'] = df_cruzado['Precio Máximo ($)'] - df_cruzado['Precio Mínimo ($)']

df_cruzado = df_cruzado.reset_index()

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df_cruzado.to_excel(writer, index=False, sheet_name='Comparativa_Cruzada')
    df_filtrado.to_excel(writer, index=False, sheet_name='Detalle_Original')

titulo_col, boton_col = st.columns([3, 1], vertical_alignment="bottom")
titulo_col.subheader(f"Evolución Diaria: {producto_sel}")
boton_col.download_button(
    label="📥 Descargar Comparativa y Desviaciones a Excel",
    data=buffer.getvalue(),
    file_name=f"comparativa_precios_{producto_sel.replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    width="stretch",
)

if colorear_por == "Bandera":
    mapa_colores = {estacion: color_bandera(estacion) for estacion in maes_sel}
else:
    mapa_colores = {}

tab_evolucion, tab_comparativa, tab_datos = st.tabs(["📈 Evolución", "📊 Comparativa", "📋 Tabla de datos"])

with tab_evolucion:
    fig = px.line(
        df_filtrado, x='Fecha', y='Precio', color='MAE_Display',
        color_discrete_map=mapa_colores, line_shape='hv' if linea_escalonada else 'linear',
        markers=mostrar_marcadores,
    )
    if mostrar_promedio:
        promedio = df_cruzado.set_index('Fecha_Dia')[columnas_estaciones].mean(axis=1)
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(promedio.index), y=promedio.values, name="Promedio",
            line=dict(color=ROJO_COPEC, width=3, dash="dash"),
            line_shape='hv' if linea_escalonada else 'linear',
        ))
    fig.update_xaxes(tickformat="%d-%m-%Y", title_text="", rangeslider=dict(visible=True, thickness=0.06))
    fig.update_yaxes(title_text="Precio (CLP)", tickprefix="$", tickformat=",")
    fig.update_layout(
        hovermode="x unified", legend_title_text='Estaciones', separators=",.", height=540,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(t=30, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption("Tip: arrastra sobre el gráfico para hacer zoom, usa la barra inferior para moverte en el tiempo "
               "y haz clic en una estación de la leyenda para ocultarla (doble clic para aislarla).")

with tab_comparativa:
    orden = resumen.sort_values('actual').reset_index()
    colores_barras = [color_bandera(e) if colorear_por == "Bandera" else None for e in orden['MAE_Display']]
    col_a, col_b = st.columns(2)

    with col_a:
        fig_actual = px.bar(
            orden, x='actual', y='MAE_Display', orientation='h', text=orden['actual'].map(pesos),
            title="Precio actual por estación",
        )
        if colorear_por == "Bandera":
            fig_actual.update_traces(marker_color=colores_barras)
        fig_actual.add_vline(x=promedio_actual, line_dash="dash", line_color=ROJO_COPEC,
                             annotation_text=f"Promedio {pesos(promedio_actual)}")
        fig_actual.update_xaxes(title_text="", tickprefix="$", tickformat=",",
                                range=[orden['actual'].min() * 0.97, orden['actual'].max() * 1.02])
        fig_actual.update_yaxes(title_text="")
        fig_actual.update_layout(separators=",.", height=max(320, 45 * len(orden)), margin=dict(l=10, r=10))
        st.plotly_chart(fig_actual, width="stretch")

    with col_b:
        orden_var = resumen.sort_values('variacion').reset_index()
        fig_var = px.bar(
            orden_var, x='variacion', y='MAE_Display', orientation='h',
            text=orden_var['variacion'].map(lambda v: f"{v:+.1f}%"),
            title="Variación en el período seleccionado",
            color=orden_var['variacion'] >= 0,
            color_discrete_map={True: ROJO_COPEC, False: "#2ecc71"},
        )
        fig_var.update_xaxes(title_text="", ticksuffix="%")
        fig_var.update_yaxes(title_text="")
        fig_var.update_layout(showlegend=False, separators=",.", height=max(320, 45 * len(orden_var)),
                              margin=dict(l=10, r=10))
        st.plotly_chart(fig_var, width="stretch")

    tabla_resumen = resumen.rename(columns={
        'inicial': 'Precio inicial', 'actual': 'Precio actual', 'minimo': 'Mínimo',
        'maximo': 'Máximo', 'variacion': 'Variación (%)',
    }).sort_values('Precio actual')
    st.dataframe(
        tabla_resumen, width="stretch",
        column_config={
            **{c: st.column_config.NumberColumn(format="$%,.0f") for c in ['Precio inicial', 'Precio actual', 'Mínimo', 'Máximo']},
            'Variación (%)': st.column_config.NumberColumn(format="%+.1f%%"),
        },
    )

with tab_datos:
    st.caption("Precio vigente por día y estación (los días sin cambio arrastran el último precio publicado).")
    st.dataframe(df_cruzado, width="stretch", hide_index=True, height=480)
