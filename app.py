import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página - Acceso directo, público y optimizado para móviles
st.set_page_config(
    page_title="Rendición de Cuentas - 6to B",
    page_icon="💰",
    layout="wide"
)

# --- FUNCIÓN PARA CARGAR Y ANONIMIZAR DATOS ---
@st.cache_data
def cargar_y_anonimizar_datos():
    ruta_excel = "data/nomina_6to_b.xlsx"
    df = pd.read_excel(ruta_excel, sheet_name="NOMINA 6TO B")
    
    # Renombrar la primera columna a Estudiante para estandarizar
    df.rename(columns={df.columns[0]: 'Estudiante'}, inplace=True)
    
    # Aseguramos eliminar nulos y transformar toda la columna a texto limpio
    df = df[df['Estudiante'].notna()]
    df['Estudiante'] = df['Estudiante'].astype(str).str.strip()
    
    # Filtramos de forma segura las filas de totales generales del Excel
    df = df[~df['Estudiante'].str.contains('TOTAL', case=False, na=False)]
    
    # FUNCIÓN DE PRIVACIDAD: Acortar el nombre para la web pública
    # Transforma "AGREDA BUENO SARAHY MATILDE" en "AGREDA SARAHY"
    def simplificar_nombre(nombre_completo):
        partes = str(nombre_completo).split()
        if len(partes) >= 3:
            # Toma el primer apellido y el primer nombre
            return f"{partes[0]} {partes[2]}"
        elif len(partes) == 2:
            return f"{partes[0]} {partes[1]}"
        return nombre_completo

    # Creamos la columna visual protegida para el buscador público
    df['Estudiante_Publico'] = df['Estudiante'].apply(simplificar_nombre)
    return df

# Control de carga del archivo
try:
    df_ingresos = cargar_y_anonimizar_datos()
except Exception as e:
    st.error(f"Error al cargar el archivo Excel: {e}")
    st.stop()

# --- REGISTRO DIRECTO DE GASTOS (EGRESOS) ---
# Puedes ir modificando o añadiendo filas a esta lista directamente aquí en tu código
gastos_data = {
    "Fecha": ["2026-05-10", "2026-05-15", "2026-06-02"],
    "Descripción / Concepto": ["Copias de exámenes de Matemáticas", "Cartelera para las fiestas patronales", "Agasajo del Día del Niño"],
    "Categoría": ["Material Académico", "Decoración", "Eventos"],
    "Monto ($)": [12.50, 25.00, 85.00]
}
df_gastos = pd.DataFrame(gastos_data)

# --- CÁLCULOS AUTOMÁTICOS DEL BALANCE ---
meses = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']

# Reemplazamos posibles valores no numéricos en los meses por 0 para sumar de forma segura
df_ingresos[meses] = df_ingresos[meses].apply(pd.to_numeric, errors='coerce').fillna(0)

total_ingresos = df_ingresos[meses].sum().sum()
total_gastos = df_gastos["Monto ($)"].sum()
saldo_disponible = total_ingresos - total_gastos

# --- INTERFAZ GRÁFICA DEL DASHBOARD ---
st.title("📊 Transparencia Financiera - 6to 'B'")
st.markdown("Plataforma abierta para la revisión y auditoría de los fondos de los padres de familia.")
st.markdown("---")

# 1. INDICADORES ECONÓMICOS PRINCIPALES (Métricas KPI)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="🟢 Total Recaudado (Ingresos)", value=f"${total_ingresos:,.2f}")
with col2:
    st.metric(label="🔴 Total Invertido (Gastos)", value=f"${total_gastos:,.2f}")
with col3:
    st.metric(
        label="🔵 Saldo Neto en Caja", 
        value=f"${saldo_disponible:,.2f}",
        delta=f"${saldo_disponible:,.2f}" if saldo_disponible >= 0 else f"-${abs(saldo_disponible):,.2f}",
        delta_color="normal"
    )

st.markdown("---")

# 2. PESTAÑAS DE NAVEGACIÓN INTERNA
tab_balance, tab_ingresos, tab_gastos = st.tabs(["📉 Balance de Caja", "💰 Control de Aportes", "💸 Detalle de Gastos"])

with tab_balance:
    st.subheader("Flujo de Efectivo del Paralelo")
    st.markdown("Visualización comparativa de los fondos administrados por el comité.")
    
    # Gráfico de barras de balance
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
    st.markdown("Seleccione el nombre de su representado para auditar que sus cuotas mensuales estén asentadas de manera correcta.")
    
    # Buscador usando los nombres protegidos para mantener la privacidad
    estudiante_sel = st.selectbox("Seleccione el alumno:", sorted(df_ingresos['Estudiante_Publico'].unique()))
    datos_alumno = df_ingresos[df_ingresos['Estudiante_Publico'] == estudiante_sel]
    
    # Mostrar tabla detallada de pagos mensuales
    st.dataframe(datos_alumno[['Estudiante_Publico'] + meses], use_container_width=True)
    
    total_alumno = datos_alumno[meses].sum(axis=1).values[0]
    st.success(f"El alumno seleccionado registra un aporte acumulado de: **${total_alumno:,.2f}**.")
    
    # Gráfico de recaudación mensual del curso
    st.markdown("---")
    st.subheader("📈 Tendencia de Recaudación Mensual")
    ingresos_por_mes = df_ingresos[meses].sum().reset_index()
    ingresos_por_mes.columns = ['Mes', 'Total Recaudado']
    
    fig_meses = px.line(ingresos_por_mes, x='Mes', y='Total Recaudado', markers=True)
    st.plotly_chart(fig_meses, use_container_width=True)

with tab_gastos:
    st.subheader("📋 Cuentas Claras: Desglose de Egresos")
    st.markdown("Lista detallada y justificada de las compras y egresos realizados por el paralelo.")
    
    # Mostrar la tabla de gastos
    st.dataframe(df_gastos, use_container_width=True)
    
    # Gráfico circular del destino de los fondos
    st.markdown("---")
    fig_gastos = px.pie(df_gastos, values='Monto ($)', names='Categoría', title='¿Cómo se distribuyen los gastos?')
    st.plotly_chart(fig_gastos, use_container_width=True)