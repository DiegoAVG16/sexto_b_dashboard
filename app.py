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
@st.cache_data(ttl=5)
def cargar_y_anonimizar_datos():
    # ID de tu enlace de Google Sheets compartido
    SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"
    SHEET_NAME = "INGRESOS" 
    
    # URL de exportación directa a formato CSV limpia
    url_csv = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    
    # Forzamos la lectura directa de la tabla tratando todo estrictamente como texto
    # Saltamos las primeras líneas si el archivo de Google tiene títulos institucionales arriba
    df = pd.read_csv(url_csv, dtype=str).fillna("0")
    
    # Estandarizamos el nombre de la primera columna que contiene los alumnos
    df.rename(columns={df.columns[0]: 'Estudiante'}, inplace=True)
    
    # Limpieza absoluta de espacios en blanco
    df['Estudiante'] = df['Estudiante'].astype(str).str.strip()
    
    # FILTRADO RADICAL: Conservamos únicamente las filas que representen nombres reales (letras)
    # y descartamos cualquier celda vacía, cabeceras rotas o la fila 42 de totales numéricos puros.
    df = df[df['Estudiante'].str.contains('[a-zA-Z]', na=False)]
    df = df[~df['Estudiante'].str.contains('TOTAL', case=False, na=False)]
    
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

# Control de carga seguro
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

# --- MAPEO SEGURO DE COLUMNAS DE APORTES MENSÚALES ---
# Mapeamos los meses que están en tu Google Sheets en orden de columnas
meses = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']

# Buscamos dinámicamente si la columna existe (por ejemplo, si se llama 'MAY' o tu columna C, D, E, etc.)
# Si no la encuentra por nombre exacto, asigna la columna por su posición física en el Excel
for i, mes in enumerate(meses):
    # Buscamos si hay alguna columna que contenga el nombre del mes
    col_encontrada = [c for c in df_ingresos.columns if mes in str(c).upper()]
    
    if col_encontrada:
        df_ingresos[mes] = pd.to_numeric(df_ingresos[col_encontrada[0]], errors='coerce').fillna(0)
    elif i + 1 < len(df_ingresos.columns):
        # Mapeo de respaldo por índice de columna física si los nombres no coinciden
        df_ingresos[mes] = pd.to_numeric(df_ingresos.iloc[:, i + 1], errors='coerce').fillna(0)
    else:
        df_ingresos[mes] = 0.0

# Cálculos globales del aula
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
    st.dataframe(df_gastos, use_container_width=True)
    
    st.markdown("---")
    fig_gastos = px.pie(df_gastos, values='Monto ($)', names='Categoría', title='¿Cómo se distribuyen los gastos del aula?')
    st.plotly_chart(fig_gastos, use_container_width=True)