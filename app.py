import streamlit as st
import pandas as pd
import io
import json
import plotly.express as px

st.set_page_config(page_title="Monitor de Precios - Chile", layout="wide")

# CSS para colores corporativos
st.markdown("""
<style>
    span[data-baseweb="tag"]:has(span[title*="COPEC"]) { background-color: #1f77b4 !important; color: white !important; }
    span[data-baseweb="tag"]:has(span[title*="SHELL"]) { background-color: #f1c40f !important; color: black !important; }
    span[data-baseweb="tag"]:has(span[title*="ARAMCO"]), span[data-baseweb="tag"]:has(span[title*="PETROBRAS"]) { background-color: #2ecc71 !important; color: white !important; }
    span[data-baseweb="tag"]:not(:has(span[title*="COPEC"])):not(:has(span[title*="SHELL"])):not(:has(span[title*="ARAMCO"])):not(:has(span[title*="PETROBRAS"])) { background-color: #95a5a6 !important; color: white !important; }
    span[data-baseweb="tag"]:has(span[title*="SHELL"]) svg { fill: black !important; }
</style>
""", unsafe_allow_html=True)

st.title("⛽ Monitor Dinámico de Precios de Combustible")

@st.cache_data(ttl=3600)
def cargar_datos_locales():
    # Leer el archivo super-comprimido en lugar del ODBC
    df = pd.read_parquet("datos_precios.parquet")
    
    # Leer la hora de actualización
    try:
        with open("info_actualizacion.json", "r") as f:
            info = json.load(f)
            hora_act = info.get("hora", "Desconocida")
    except:
        hora_act = "Desconocida"
        
    return df, hora_act

try:
    df_raw, hora_actualizacion = cargar_datos_locales()
    st.info(f"Última actualización de precios desde la base central: **{hora_actualizacion}**")
except Exception as e:
    st.error(f"Error al leer los datos: {e}. Asegúrate de haber subido 'datos_precios.parquet'.")
    df_raw = pd.DataFrame(columns=['MAE_Display', 'Producto', 'Precio', 'Fecha'])

st.sidebar.header("Filtros del Panel")

if not df_raw.empty:
    productos_disponibles = sorted(df_raw['Producto'].dropna().unique())
    producto_sel = st.sidebar.selectbox("Selecciona Producto", productos_disponibles)

    maes_disponibles = sorted(df_raw['MAE_Display'].unique())
    maes_sel = st.sidebar.multiselect(
        "Selecciona Estaciones", 
        options=maes_disponibles,
        default=maes_disponibles[:3] if len(maes_disponibles) >= 3 else maes_disponibles
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Rango de Fechas**")
    fecha_min = df_raw['Fecha'].min().date()
    fecha_max = df_raw['Fecha'].max().date()

    f_inicio = st.sidebar.date_input("Desde:", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
    f_fin = st.sidebar.date_input("Hasta:", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
    st.sidebar.markdown("---")

    if f_inicio <= f_fin:
        df_filtrado = df_raw[
            (df_raw['Producto'] == producto_sel) &
            (df_raw['MAE_Display'].isin(maes_sel)) &
            (df_raw['Fecha'].dt.date >= f_inicio) &
            (df_raw['Fecha'].dt.date <= f_fin)
        ].sort_values('Fecha')
    else:
        st.sidebar.error("La fecha 'Desde' debe ser anterior a 'Hasta'.")
        df_filtrado = pd.DataFrame()

    if not df_filtrado.empty:
        st.subheader(f"Evolución Diaria: {producto_sel}")
        
        mapa_colores = {}
        for estacion in maes_sel:
            est_upper = estacion.upper()
            if 'COPEC' in est_upper: mapa_colores[estacion] = '#1f77b4' 
            elif 'SHELL' in est_upper: mapa_colores[estacion] = '#f1c40f' 
            elif 'ARAMCO' in est_upper or 'PETROBRAS' in est_upper: mapa_colores[estacion] = '#2ecc71' 
            else: mapa_colores[estacion] = '#95a5a6'
        
        fig = px.line(
            df_filtrado, x='Fecha', y='Precio', color='MAE_Display',
            color_discrete_map=mapa_colores, line_shape='hv'
        )
        fig.update_xaxes(tickformat="%d-%m-%Y", title_text="")
        fig.update_yaxes(title_text="Precio (CLP)")
        fig.update_layout(hovermode="x unified", legend_title_text='Estaciones')
        
        st.plotly_chart(fig, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Precios_Diarios')
        
        st.download_button(
            label="📥 Descargar datos filtrados a Excel",
            data=buffer.getvalue(),
            file_name=f"precios_diarios_{producto_sel.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Selecciona al menos un código MAE (y un rango de fechas válido).")