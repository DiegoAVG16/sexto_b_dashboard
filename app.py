import streamlit as st
import pandas as pd
import plotly.express as px
import time

# Configuración de la interfaz del dashboard
st.set_page_config(
    page_title="Transparencia Financiera - 6to B",
    page_icon="💰",
    layout="wide"
)

# ID extraído de tu enlace directo de Google Sheets
SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"

# Parámetros numéricos de pestañas (GIDs) oficiales
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

def descargar_pestaña(gid):
    """Descarga una pestaña específica usando el endpoint de exportación limpia"""
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}&t={int(time.time())}"
    try:
        # Dejamos que pandas detecte las cabeceras automáticamente de la primera fila
        df = pd.read_csv(url, dtype=str).fillna("0")
        # Limpiamos los nombres de las columnas eliminando espacios ocultos
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()

def cargar_ingresos():
    df = descargar_pestaña(GID_INGRESOS)
    meses = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']
    
    # Si la hoja no tiene la columna de estudiantes, devolvemos estructura vacía
    if df.empty or df.columns[0] not in df.columns:
        # Intentar acoplar si la primera columna tiene otro nombre (ej. 'NOMINA 6TO B')
        if not df.empty:
            df.rename(columns={df.columns[0]: 'Estudiante'}, inplace=True)
        else:
            return pd.DataFrame(columns=['Estudiante'] + meses + ['Estudiante_Publico'])

    # Forzar el nombre de la primera columna a 'Estudiante' por si acaso
    df.rename(columns={df.columns[0]: 'Estudiante'}, inplace=True)
    
    lista_ingresos = []
    for _, fila in df.iterrows():
        nombre = str(fila['Estudiante']).strip()
        
        # Filtro estricto para ignorar totales o celdas vacías de control
        if nombre in ["0", "", "nan"] or "TOTAL" in nombre.upper() or "NOMINA" in nombre.upper():
            continue
            
        registro = {'Estudiante': nombre}
        for m in meses:
            if m in df.columns:
                registro[m] = limpiar_monto(fila[m])
            else:
                registro[m] = 0.0
        lista_ingresos.append(registro)
        
    if not lista_ingresos:
        return pd.DataFrame(columns=['Estudiante'] + meses + ['Estudiante_Publico'])
        
    df_res = pd.DataFrame(lista_ingresos)
    
    # Formateo de privacidad para el buscador público (Primer Nombre + Primer Apellido)
    def simplificar_nombre(n):
        partes = str(n).split()
        return f"{partes[0]} {partes[2]}" if len(partes) >= 3 else n
    df_res['Estudiante_Publico'] = df_res['Estudiante'].apply(simplificar_nombre)
    return df_res

def cargar_egresos():
    df = descargar_pestaña(GID_EGRESOS)
    df_vacio = pd.DataFrame(columns=["Concepto / Descripción", "Mes", "Monto ($)"])
    
    if df.empty:
        return df_vacio
        
    # Forzar el nombre de la primera columna a 'Concepto'
    df.rename(columns={df.columns[0]: 'Concepto'}, inplace=True)
    meses_egresos = ['MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE', 'ENERO', 'FEBRERO']
    
    lista_gastos = []
    for _, fila in df.iterrows():
        concepto = str(fila['Concepto']).strip()
        
        if concepto in ["0", "", "nan"] or "TOTAL" in concepto.upper() or "OBS" in concepto.upper():
            continue
            
        for m in meses_egresos:
            if m in df.columns:
                monto = limpiar_monto(fila[m])
                if monto > 0:
                    lista_gastos.append({
                        "Concepto / Descripción": concepto,
                        "Mes": m.capitalize(),
                        "Monto ($)": monto
                    })
                    
    if not lista_gastos:
        return df_vacio
        
    return pd.DataFrame(lista_gastos)

# --- PROCESAMIENTO SEGURO DE DATOS ---
df_ingresos = cargar_ingresos()
df_gastos = cargar_egresos()

meses_cols = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']

# Operaciones matemáticas globales
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