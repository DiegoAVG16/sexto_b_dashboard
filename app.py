import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Rendición de Cuentas - 6to B",
    page_icon="💰",
    layout="wide"
)

# --- FUNCIÓN PARA CARGAR DESDE GOOGLE SHEETS EN TIEMPO REAL ---
# Reducimos al mínimo el tiempo de caché para forzar la actualización
@st.cache_data(ttl=2)  
def cargar_y_anonimizar_datos():
    SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"
    SHEET_NAME = "INGRESOS" 
    
    # URL de exportación directa a CSV apuntando a la pestaña correcta
    url_csv = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    
    # 1. Leemos todo tratándolo estrictamente como texto/string desde el inicio
    df_raw = pd.read_csv(url_csv, header=None, dtype=str).fillna("")
    
    # 2. Buscamos de forma manual la fila donde arranca la cabecera real
    fila_header = 0
    for idx, row in df_raw.iterrows():
        valores_fila = [str(val).upper().strip() for val in row.values]
        if any('NOMINA' in s or 'ESTUDIANTE' in s or 'MAY' in s for s in valores_fila):
            fila_header = idx
            break
            
    # 3. Cargamos el DataFrame definitivo saltando las filas decorativas superiores
    df = pd.read_csv(url_csv, skiprows=fila_header)
    
    # Forzamos que la primera columna se llame Estudiante
    df.rename(columns={df.columns[0]: 'Estudiante'}, inplace=True)
    
    # Limpieza de espacios y eliminación de registros nulos en nombres
    df = df[df['Estudiante'].notna()]
    df['Estudiante'] = df['Estudiante'].astype(str).str.strip()
    
    # FILTRADO DE TOTALES: Eliminamos la fila 42 que tiene los totales numéricos sueltos
    df = df[~df['Estudiante'].str.contains('TOTAL', case=False, na=False)]
    df = df[df['Estudiante'].str.contains('[a-zA-Z]', na=False)] # Solo nombres con letras reales
    
    # FUNCIÓN DE PRIVACIDAD: Conservar solo Primer Apellido y Primer Nombre
    def simplificar_nombre(nombre_completo):
        partes = str(nombre_completo).split()
        if len(partes) >= 3:
            return f"{partes[0]} {partes[2]}"
        elif len(partes) == 2:
            return f"{partes[0]} {partes[1]}"
        return nombre_completo

    df['Estudiante_Publico'] = df['Estudiante'].apply(simplificar_nombre)
    return df

# Control de carga
try:
    df_ingresos = cargar_y_anonimizar_datos()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets en tiempo real: {e}")
    st.stop()

# --- REGISTRO DIRECTO DE GASTOS (EGRESOS) ---
gastos_data = {
    "Fecha": ["2026-05-10", "2026-05-15", "2026-06-02"],
    "Descripción / Concepto": ["Copias de exámenes de Matemáticas", "Cartelera para las fiestas patronales", "Agasajo del Día del Niño"],
    "Categoría": ["Material Académico", "Decoración", "Eventos"],
    "Monto ($)": [12.50, 25.00, 85.00]
}
df_gastos = pd.DataFrame(gastos_data)

# --- CÁLCULOS AUTOMÁTICOS DEL BALANCE DE CAJA ---
meses = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']

# Conversión y limpieza de los aportes de las columnas mensuales
for mes in meses:
    if mes in df_ingresos.columns:
        df_ingresos[mes] = pd.to_numeric(df_ingresos[mes], errors='coerce').fillna(0)
    else:
        df_ingresos[mes] = 0.0

total_ingresos = df_ingresos[meses].sum().sum()
total_gastos = df_gastos["Monto ($)"].sum()
saldo_disponible = total_ingresos - total_gastos

# --- INTERFAZ GRÁFICA DEL DASHBOARD ---
st.title("📊 Transparencia Financiera - 6to 'B'")
st.markdown("Plataforma abierta para la revisión y auditoría de fondos en tiempo real.")
st.markdown("---")

# 1. BLOQUE DE MÉTRICAS GENERALES
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="🟢 Total Recaudado (Ingresos)", value=f"${total_ingresos:,.2f}")
with col2:
    st.metric(label="🔴 Total Invertido (Gastos)", value=f"${total_gastos:,.2f}")
with col3:
    st.metric(
        label="🔵 Saldo Neto Disponible en Caja", 
        value=f"${saldo_disponible:,.2f}",
        delta=f"${saldo_disponible:,.2f}" if saldo_disponible >= 0 else f"-${abs(saldo_disponible):,.2f}",
        delta_color="normal"
    )

st.markdown("---")

# 2. PESTAÑAS DE NAVEGACIÓN
tab_balance, tab_ingresos, tab_gastos = st.tabs(["📉 Balance de Caja", "💰 Control de Aportes", "💸 Detalle de Gastos"])

with tab_balance:
    st.subheader("Flujo de Efectivo Mensual")
    st.markdown("Comparativa global de ingresos frente a egresos registrados por el comité.")
    
    df_comparativo = pd.DataFrame({
        "Concepto": ["Ingresos Totales", "Gastos Totales"],
        "Valor ($)": [total_ingresos, total_gastos],
        "Tipo": ["Ingresos", "Gastos"]
    })
    
    fig_balance = px.bar(
        df_comparativo, 
        x="Concepto", 
        y="Valor ($)", 
        color="Tipo",
        color_discrete_map={"Ingresos": "#2ecc71", "Gastos": "#e74c3c"},
        text_auto='.2f'
    )
    st.plotly_chart(fig_balance, use_container_width=True)

with tab_ingresos:
    st.subheader("🔍 Verificación de Aportes por Alumno")
    st.markdown("Seleccione el nombre de su representado para constatar que sus cuotas mensuales estén debidamente asentadas.")
    
    estudiante_sel = st.selectbox("Seleccione el alumno:", sorted(df_ingresos['Estudiante_Publico'].unique()))
    datos_alumno = df_ingresos[df_ingresos['Estudiante_Publico'] == estudiante_sel]
    
    st.dataframe(datos_alumno[['Estudiante_Publico'] + meses], use_container_width=True)
    
    total_alumno = datos_alumno[meses].sum(axis=1).values[0]
    st.success(f"El alumno seleccionado registra un aporte acumulado de: **${total_alumno:,.2f}**.")
    
    st.markdown("---")
    st.subheader("📈 Tendencia de Recaudación Mensual")
    ingresos_por_mes = df_ingresos[meses].sum().reset_index()
    ingresos_por_mes.columns = ['Mes', 'Total Recaudado']
    
    fig_meses = px.line(ingresos_por_mes, x='Mes', y='Total Recaudado', markers=True)
    st.plotly_chart(fig_meses, use_container_width=True)

with tab_gastos:
    st.subheader("📋 Cuentas Claras: Desglose de Egresos")
    st.markdown("Lista detallada y justificada de las compras, adquisiciones o egresos del aula.")
    
    st.dataframe(df_gastos, use_container_width=True)
    
    st.markdown("---")
    fig_gastos = px.pie(df_gastos, values='Monto ($)', names='Categoría', title='¿Cómo se distribuyen los gastos del aula?')
    st.plotly_chart(fig_gastos, use_container_width=True)