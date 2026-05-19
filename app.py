import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página del dashboard
st.set_page_config(
    page_title="Rendición de Cuentas - 6to B",
    page_icon="💰",
    layout="wide"
)

# ID único de tu documento de Google Sheets
SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"

# Mapeo estricto de meses según la estructura visual de tus dos hojas de cálculo
# Columna B = Mayo (Índice 1), Columna C = Junio (Índice 2), Columna D = Julio (Índice 3), etc.
MAPEO_MESES = {
    'MAYO': 1,
    'JUNIO': 2,
    'JULIO': 3,
    'AGOSTO': 4,
    'SEPTIEMBRE': 5,
    'OCTUBRE': 6,
    'NOVIEMBRE': 7,
    'DICIEMBRE': 8,
    'ENERO': 9,
    'FEBRERO': 10
}

# --- FUNCIÓN PARA CARGAR INGRESOS (TABLA DE ALUMNOS) ---
@st.cache_data(ttl=2)
def cargar_ingresos():
    # Descarga directa de la primera pestaña usando gid=0
    url_ingresos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
    
    # Leemos el CSV sin saltar filas para mapear la estructura limpia desde la fila 2
    df = pd.read_csv(url_ingresos, header=None, dtype=str).fillna("0")
    
    # La nómina real de alumnos empieza desde la fila indexada como 2 (Fila 3 de Sheets)
    # Fila 0: cabecera vacía o título, Fila 1: Cabeceras de meses (A1=OBS, B1=MAYO, etc.)
    df_datos = df.iloc[2:].copy()
    
    lista_ingresos_limpios = []
    
    for _, fila in df_datos.iterrows():
        nombre_estudiante = str(fila.iloc[0]).strip()
        
        # Saltamos filas de control, totales finales de la hoja o celdas vacías
        if nombre_estudiante == "0" or nombre_estudiante == "" or "TOTAL" in nombre_estudiante.upper():
            continue
            
        # Construimos el diccionario base del estudiante
        registro = {'Estudiante': nombre_estudiante}
        
        # Extraemos el valor numérico exacto asignado a cada mes por su posición de columna
        for mes_nombre, col_indice in MAPEO_MESES.items():
            if col_indice < len(fila):
                valor_texto = str(fila.iloc[col_indice]).replace('$', '').replace(',', '').strip()
                try:
                    registro[mes_nombre] = float(valor_texto)
                except ValueError:
                    registro[mes_nombre] = 0.0
            else:
                registro[mes_nombre] = 0.0
                
        lista_ingresos_limpios.append(registro)
        
    if not lista_ingresos_limpios:
        return pd.DataFrame(columns=['Estudiante'] + list(MAPEO_MESES.keys()))
        
    df_resultado = pd.DataFrame(lista_ingresos_limpios)
    
    # Función para acortar nombres en la vista pública del aula
    def simplificar_nombre(nombre_completo):
        partes = str(nombre_completo).split()
        if len(partes) >= 3:
            return f"{partes[0]} {partes[2]}"
        elif len(partes) == 2:
            return f"{partes[0]} {partes[1]}"
        return nombre_completo

    df_resultado['Estudiante_Publico'] = df_resultado['Estudiante'].apply(simplificar_nombre)
    return df_resultado


# --- FUNCIÓN PARA CARGAR EGRESOS (TABLA DE GASTOS) ---
@st.cache_data(ttl=2)
def cargar_egresos():
    # Descarga limpia apuntando directamente a la pestaña por su nombre string
    url_egresos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=EGRESOS"
    
    df = pd.read_csv(url_egresos, header=None, dtype=str).fillna("0")
    
    # Descartamos la fila de cabecera de texto (Fila 0) para procesar los registros puros
    df_datos = df.iloc[1:].copy()
    
    lista_gastos = []
    
    for _, fila in df_datos.iterrows():
        concepto = str(fila.iloc[0]).strip()
        
        # Evitamos leer filas vacías o la fila de totales calculados del propio Sheets
        if concepto == "0" or concepto == "" or "TOTAL" in concepto.upper():
            continue
            
        # Buscamos gastos mes por mes según las posiciones fijas de las columnas
        for mes_nombre, col_indice in MAPEO_MESES.items():
            if col_indice < len(fila):
                valor_texto = str(fila.iloc[col_indice]).replace('$', '').replace(',', '').strip()
                try:
                    monto = float(valor_texto)
                except ValueError:
                    monto = 0.0
                    
                if monto > 0:
                    lista_gastos.append({
                        "Concepto / Descripción": concepto,
                        "Mes Correspondiente": mes_nombre.capitalize(),
                        "Monto ($)": monto
                    })
                    
    if not lista_gastos:
        return pd.DataFrame(columns=["Concepto / Descripción", "Mes Correspondiente", "Monto ($)"])
        
    return pd.DataFrame(lista_gastos)


# --- CONTROL DE EJECUCIÓN FINANCIERA ---
try:
    df_ingresos = cargar_ingresos()
    df_gastos = cargar_egresos()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets en tiempo real: {e}")
    st.stop()


# --- OPERACIONES CRUCIALES DE SUMA Y TOTALIZACIÓN ---
meses_lista = list(MAPEO_MESES.keys())

# Sumamos horizontal y verticalmente la matriz de ingresos puros calculados por Python
total_ingresos = df_ingresos[meses_lista].sum().sum()

# Sumamos la columna de montos de la lista estructurada de gastos de Python
total_gastos = df_gastos["Monto ($)"].sum() if not df_gastos.empty else 0.0

# Cálculo del saldo real en caja
saldo_disponible = total_ingresos - total_gastos


# --- INTERFAZ DEL DASHBOARD EN STREAMLIT ---
st.title("📊 Transparencia Financiera - 6to 'B'")
st.markdown("Plataforma abierta para la revisión y auditoría de fondos de los padres de familia.")
st.markdown("---")

# 1. BLOQUE DE MÉTRICAS PRINCIPALES
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

# 2. PESTAÑAS DE NAVEGACIÓN DEL USUARIO
tab_balance, tab_ingresos, tab_gastos = st.tabs(["% Balance de Caja", "🏦 Control de Aportes", "📋 Detalle de Gastos"])

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
    if not df_ingresos.empty:
        estudiante_sel = st.selectbox("Seleccione el alumno:", sorted(df_ingresos['Estudiante_Publico'].unique()))
        datos_alumno = df_ingresos[df_ingresos['Estudiante_Publico'] == estudiante_sel]
        
        st.dataframe(datos_alumno[['Estudiante_Publico'] + meses_lista], use_container_width=True)
        
        total_alumno = datos_alumno[meses_lista].sum(axis=1).values[0]
        st.success(f"El alumno seleccionado registra un aporte acumulado de: **${total_alumno:,.2f}**.")
    else:
        st.info("No hay datos de alumnos procesados.")
    
    st.markdown("---")
    st.subheader("📈 Tendencia de Recaudación Mensual")
    ingresos_por_mes = df_ingresos[meses_lista].sum().reset_index()
    ingresos_por_mes.columns = ['Mes', 'Total Recaudado']
    fig_meses = px.line(ingresos_por_mes, x='Mes', y='Total Recaudado', markers=True)
    st.plotly_chart(fig_meses, use_container_width=True)

with tab_gastos:
    st.subheader("📋 Cuentas Claras: Desglose de Egresos")
    if not df_gastos.empty:
        st.dataframe(df_gastos, use_container_width=True)
        st.markdown("---")
        fig_gastos = px.pie(
            df_gastos, 
            values='Monto ($)', 
            names='Concepto / Descripción', 
            title='¿Cómo se distribuyen los egresos del aula?'
        )
        st.plotly_chart(fig_gastos, use_container_width=True)
    else:
        st.info("No se registran egresos guardados en la hoja de Google Sheets actualmente.")