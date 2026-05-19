import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
import time

# Configuración de la interfaz del dashboard
st.set_page_config(
    page_title="Transparencia Financiera - 6to B",
    page_icon="💰",
    layout="wide"
)

# Parámetros numéricos internos de pestaña (GIDs) oficiales de tu documento
GID_INGRESOS = "0"
GID_EGRESOS = "1460599602"  

# Mapeo posicional exacto para la pestaña de INGRESOS
MAPEO_INGRESOS = {
    'MAY': 1, 'JUN': 2, 'JUL': 3, 'AGO': 4, 'SEP': 5,
    'OCT': 6, 'NOV': 7, 'DIC': 8, 'ENE': 9, 'FEB': 10
}

# Mapeo posicional exacto para la pestaña de EGRESOS
MAPEO_EGRESOS = {
    'MAYO': 1, 'JUNIO': 2, 'JULIO': 3, 'AGOSTO': 4, 'SEPTIEMBRE': 5,
    'OCTUBRE': 6, 'NOVIEMBRE': 7, 'DICIEMBRE': 8, 'ENERO': 9, 'FEBRERO': 10
}

def descargar_csv(gid):
    """Descarga el CSV usando la URL de publicación limpia sin espacios y rompiendo la caché"""
    # URL unificada rigurosamente sin espacios intermedios
    url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vQvB8RfFCeQKwZ9sT7tag7KSyOCVAakAZqAmVr4epUoHM0PwvpUkc4AzoQm9Xnce5jXF9ojROOLUMv7/pub?output=csv&gid={gid}&t={int(time.time())}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Reemplazar valores nulos por "0" string de manera segura
            return pd.read_csv(io.StringIO(response.text), header=None, dtype=str).fillna("0")
        return pd.DataFrame()
    except Exception as e:
        # Evita que la app colapse en blanco si hay problemas de red
        st.sidebar.error(f"Error de conexión en pestaña {gid}")
        return pd.DataFrame()

def cargar_ingresos():
    df = descargar_csv(GID_INGRESOS)
    if df.empty or len(df) <= 2:
        return pd.DataFrame(columns=['Estudiante'] + list(MAPEO_INGRESOS.keys()) + ['Estudiante_Publico'])
        
    lista_ingresos = []
    df_datos = df.iloc[2:].copy() 
    
    for _, fila in df_datos.iterrows():
        if len(fila) <= 1:
            continue
        nombre = str(fila.iloc[0]).strip()
        
        if nombre == "0" or nombre == "" or "TOTAL" in nombre.upper() or "NOMINA" in nombre.upper():
            continue
            
        registro = {'Estudiante': nombre}
        for mes_nombre, col_idx in MAPEO_INGRESOS.items():
            if col_idx < len(fila):
                valor = str(fila.iloc[col_idx]).replace('$', '').replace(',', '').strip()
                try:
                    registro[mes_nombre] = float(valor) if valor not in ["0", ""] else 0.0
                except ValueError:
                    registro[mes_nombre] = 0.0
            else:
                registro[mes_nombre] = 0.0
        lista_ingresos.append(registro)
        
    if not lista_ingresos:
        return pd.DataFrame(columns=['Estudiante'] + list(MAPEO_INGRESOS.keys()) + ['Estudiante_Publico'])
        
    df_res = pd.DataFrame(lista_ingresos)
    
    def simplificar_nombre(n):
        partes = str(n).split()
        return f"{partes[0]} {partes[2]}" if len(partes) >= 3 else n
    df_res['Estudiante_Publico'] = df_res['Estudiante'].apply(simplificar_nombre)
    return df_res

def cargar_egresos():
    df = descargar_csv(GID_EGRESOS)
    df_vacio = pd.DataFrame(columns=["Concepto / Descripción", "Mes", "Monto ($)"])
    
    if df.empty or len(df) <= 1:
        return df_vacio
        
    lista_gastos = []
    df_datos = df.iloc[1:].copy()
    
    for _, fila in df_datos.iterrows():
        if fila.empty or pd.isna(fila.iloc[0]):
            continue
        concepto = str(fila.iloc[0]).strip()
        
        if concepto == "0" or concepto == "" or "TOTAL" in concepto.upper() or "OBS" in concepto.upper():
            continue
            
        for mes_nombre, col_idx in MAPEO_EGRESOS.items():
            if col_idx < len(fila):
                valor = str(fila.iloc[col_idx]).replace('$', '').replace(',', '').strip()
                try:
                    monto = float(valor) if valor not in ["0", ""] else 0.0
                except ValueError:
                    monto = 0.0
                    
                if monto > 0:
                    lista_gastos.append({
                        "Concepto / Descripción": concepto,
                        "Mes": mes_nombre.capitalize(),
                        "Monto ($)": monto
                    })
                    
    if not lista_gastos:
        return df_vacio
        
    return pd.DataFrame(lista_gastos)

# --- PROCESAMIENTO SEGURO DE DATOS ---
df_ingresos = cargar_ingresos()
df_gastos = cargar_egresos()

meses_cols = list(MAPEO_INGRESOS.keys())
for col in meses_cols:
    if col not in df_ingresos.columns:
        df_ingresos[col] = 0.0

# Operaciones de agregación matemática
total_ingresos = float(df_ingresos[meses_cols].sum().sum()) if not df_ingresos.empty else 0.0
total_gastos = float(df_gastos["Monto ($)"].sum()) if (not df_gastos.empty and "Monto ($)" in df_gastos.columns) else 0.0
saldo_caja = total_ingresos - total_gastos

# --- INTERFAZ GRÁFICA (STREAMLIT) ---
st.title("📊 Transparencia Financiera - 6to 'B'")
st.markdown("Plataforma abierta para la revisión y auditoría de fondos de los padres de familia.")
st.markdown("---")

# Fila superior de tarjetas de métricas (KPIs)
col_inc_1, col_inc_2, col_inc_3 = st.columns(3)
with col_inc_1:
    st.metric(label="🟢 Total Recaudado (Ingresos)", value=f"${total_ingresos:,.2f}")
with col_inc_2:
    st.metric(label="🔴 Total Invertido (Gastos)", value=f"${total_gastos:,.2f}")
with col_inc_3:
    st.metric(label="🔵 Saldo Neto Disponible en Caja", value=f"${saldo_caja:,.2f}")

st.markdown("---")

# Estructura modular por pestañas
pestaña_balance, pestaña_aportes, pestaña_egresos = st.tabs(["📉 Balance de Caja", "💰 Control de Aportes", "📋 Detalle de Gastos"])

with pestaña_balance:
    st.subheader("Flujo de Efectivo Mensual")
    df_balance = pd.DataFrame({
        "Tipo": ["Ingresos Acumulados", "Gastos Acumulados"],
        "Monto ($)": [total_ingresos, total_gastos]
    })
    fig_balance = px.bar(
        df_balance, x="Tipo", y="Monto ($)", color="Tipo",
        color_discrete_map={"Ingresos Acumulados": "#2ecc71", "Gastos Acumulados": "#e74c3c"}, text_auto='.2f'
    )
    st.plotly_chart(fig_balance, use_container_width=True)

with pestaña_aportes:
    st.subheader("🔍 Buscador de Aportes por Estudiante")
    if 'Estudiante_Publico' in df_ingresos.columns and not df_ingresos.empty and len(df_ingresos['Estudiante_Publico'].unique()) > 0:
        estudiante_sel = st.selectbox("Seleccione el alumno para verificar sus pagos:", sorted(df_ingresos['Estudiante_Publico'].dropna().unique()))
        filtro = df_ingresos[df_ingresos['Estudiante_Publico'] == estudiante_sel]
        st.dataframe(filtro[['Estudiante'] + meses_cols], use_container_width=True)
        total_estudiante = filtro[meses_cols].sum(axis=1).values[0] if not filtro.empty else 0.0
        st.success(f"Aporte total entregado por el representante a la fecha: **${total_estudiante:,.2f}**")
    else:
        st.info("No se encontraron registros de estudiantes en la lista de ingresos.")

with pestaña_egresos:
    st.subheader("📋 Cuentas Claras: Desglose de Egresos")
    if not df_gastos.empty and "Monto ($)" in df_gastos.columns:
        st.dataframe(df_gastos, use_container_width=True)
        fig_pie = px.pie(df_gastos, values='Monto ($)', names='Concepto / Descripción', title='¿Cómo se distribuyen los gastos del aula?')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No se registran egresos guardados en la hoja de Google Sheets actualmente.")