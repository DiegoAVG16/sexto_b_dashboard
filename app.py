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

# ID extraído de tu enlace directo de Google Sheets
SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"

# IDs numéricos específicos de tus pestañas (GIDs)
GID_INGRESOS = "0"
GID_EGRESOS = "1460599602"  

def limpiar_monto(valor):
    """Convierte texto de la hoja a números flotantes de forma segura"""
    if pd.isna(valor):
        return 0.0
    val_clean = str(valor).replace('$', '').replace(',', '').strip()
    try:
        return float(val_clean) if val_clean not in ["", "0", "0.00"] else 0.0
    except ValueError:
        return 0.0

def descargar_pestaña_csv(gid):
    """Descarga el contenido de una pestaña usando el endpoint de exportación nativo"""
    # Usamos un parámetro de tiempo aleatorio para obligar a Google a enviar los datos más recientes sin usar caché
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}&t={int(time.time())}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # Leemos forzando que todo sea texto para evitar transformaciones erróneas de Pandas
            df = pd.read_csv(io.StringIO(response.text), header=None, dtype=str).fillna("0")
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def cargar_ingresos():
    df = descargar_pestaña_csv(GID_INGRESOS)
    meses_ingresos = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']
    
    if df.empty or len(df) <= 1:
        return pd.DataFrame(columns=['Estudiante'] + meses_ingresos + ['Estudiante_Publico'])
        
    # Mapeo posicional estricto: Columna A (0) Nombres, Columna B (1) MAY, etc.
    lista_ingresos = []
    df_datos = df.iloc[1:].copy() # Saltamos la fila 0 de cabeceras
    
    for _, fila in df_datos.iterrows():
        if len(fila) == 0:
            continue
        nombre = str(fila.iloc[0]).strip()
        
        if nombre in ["0", "", "nan"] or "TOTAL" in nombre.upper() or "NOMINA" in nombre.upper():
            continue
            
        registro = {'Estudiante': nombre}
        for i, mes in enumerate(meses_ingresos, start=1):
            if i < len(fila):
                registro[mes] = limpiar_monto(fila.iloc[i])
            else:
                registro[mes] = 0.0
        lista_ingresos.append(registro)
        
    if not lista_ingresos:
        return pd.DataFrame(columns=['Estudiante'] + meses_ingresos + ['Estudiante_Publico'])
        
    df_res = pd.DataFrame(lista_ingresos)
    
    # Simplificación de privacidad: Primer Nombre y Primer Apellido
    def simplificar_nombre(n):
        partes = str(n).split()
        return f"{partes[0]} {partes[2]}" if len(partes) >= 3 else n
    df_res['Estudiante_Publico'] = df_res['Estudiante'].apply(simplificar_nombre)
    return df_res

def cargar_egresos():
    df = descargar_pestaña_csv(GID_EGRESOS)
    df_vacio = pd.DataFrame(columns=["Concepto / Descripción", "Mes", "Monto ($)"])
    
    if df.empty or len(df) <= 1:
        return df_vacio
        
    # Mapeo para la pestaña de egresos (Columna A: Concepto, Columna B: MAYO, etc.)
    meses_egresos = ['MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE', 'ENERO', 'FEBRERO']
    
    lista_gastos = []
    df_datos = df.iloc[1:].copy() # Saltamos la fila de cabeceras de la segunda pestaña
    
    for _, fila in df_datos.iterrows():
        if len(fila) == 0:
            continue
        concepto = str(fila.iloc[0]).strip()
        
        if concepto in ["0", "", "nan"] or "TOTAL" in concepto.upper() or "OBS" in concepto.upper():
            continue
            
        for i, mes in enumerate(meses_egresos, start=1):
            if i < len(fila):
                monto = limpiar_monto(fila.iloc[i])
                if monto > 0:
                    lista_gastos.append({
                        "Concepto / Descripción": concepto,
                        "Mes": mes.capitalize(),
                        "Monto ($)": monto
                    })
                    
    if not lista_gastos:
        return df_vacio
        
    return pd.DataFrame(lista_gastos)

# --- PROCESAMIENTO SEGURO DE DATOS ---
df_ingresos = cargar_ingresos()
df_gastos = cargar_egresos()

meses_cols = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']

# Operaciones matemáticas con validación de existencia
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