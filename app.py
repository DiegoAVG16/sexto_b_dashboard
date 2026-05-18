import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página - Acceso directo, público y optimizado para dispositivos móviles
st.set_page_config(
    page_title="Rendición de Cuentas - 6to B",
    page_icon="💰",
    layout="wide"
)

# --- FUNCIÓN PARA CARGAR DESDE GOOGLE SHEETS EN TIEMPO REAL ---
@st.cache_data(ttl=30)  # El caché se actualizará automáticamente cada 30 segundos si hay cambios en Google Sheets
def cargar_y_anonimizar_datos():
    # ID extraído directamente de tu enlace compartido
    SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"
    SHEET_NAME = "NOMINA 6TO B" 
    
    # Construcción de la URL de exportación directa en formato CSV
    url_csv = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME.replace(' ', '%20')}"
    
    # 1. Lectura inicial en bruto para escanear y encontrar los encabezados de las columnas
    df_raw = pd.read_csv(url_csv, header=None)
    
    # 2. Localización dinámica de la fila donde se ubican la Nómina o los meses
    fila_header = 0
    for idx, row in df_raw.iterrows():
        row_str = row.astype(str).str.upper().values
        if any('NOMINA' in s or 'MAY' in s for s in row_str):
            fila_header = idx
            break
            
    # 3. Recarga y procesamiento del archivo saltando las filas superiores vacías o con títulos institucionales
    df = pd.read_csv(url_csv, skiprows=fila_header)
    
    # Renombrar la primera columna para estandarizar el buscador
    df.rename(columns={df.columns[0]: 'Estudiante'}, inplace=True)
    
    # Limpieza: Eliminamos nulos y transformamos la nómina en texto plano sin espacios residuales
    df = df[df['Estudiante'].notna()]
    df['Estudiante'] = df['Estudiante'].astype(str).str.strip()
    
    # Exclusión de seguridad para evitar que las filas de totales generales del Excel rompan las métricas
    df = df[~df['Estudiante'].str.contains('TOTAL', case=False, na=False)]
    
    # FUNCIÓN DE PRIVACIDAD: Acortar nombres para que el dashboard sea de acceso libre seguro
    def simplificar_nombre(nombre_completo):
        partes = str(nombre_completo).split()
        if len(partes) >= 3:
            # Devuelve: Primer Apellido + Primer Nombre
            return f"{partes[0]} {partes[2]}"
        elif len(partes) == 2:
            return f"{partes[0]} {partes[1]}"
        return nombre_completo

    # Generamos la columna anonimizada con la que interactuarán los representantes
    df['Estudiante_Publico'] = df['Estudiante'].apply(simplificar_nombre)
    return df

# Control y manejo de excepciones en la carga del servidor
try:
    df_ingresos = cargar_y_anonimizar_datos()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets en tiempo real: {e}")
    st.stop()

# --- REGISTRO DIRECTO DE GASTOS (EGRESOS) ---
# Puedes modificar o añadir nuevas filas a este diccionario cada vez que realicen un gasto en el paralelo
gastos_data = {
    "Fecha": ["2026-05-10", "2026-05-15", "2026-06-02"],
    "Descripción / Concepto": ["Copias de exámenes de Matemáticas", "Cartelera para las fiestas patronales", "Agasajo del Día del Niño"],
    "Categoría": ["Material Académico", "Decoración", "Eventos"],
    "Monto ($)": [12.50, 25.00, 85.00]
}
df_gastos = pd.DataFrame(gastos_data)

# --- CÁLCULOS AUTOMÁTICOS DEL BALANCE DE CAJA ---
meses = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']

# Forzamos la conversión a datos numéricos en las celdas de meses para evitar errores por textos accidentales
df_ingresos[meses] = df_ingresos[meses].apply(pd.to_numeric, errors='coerce').fillna(0)

total_ingresos = df_ingresos[meses].sum().sum()
total_gastos = df_gastos["Monto ($)"].sum()
saldo_disponible = total_ingresos - total_gastos

# --- INTERFAZ GRÁFICA DEL DASHBOARD ---
st.title("📊 Transparencia Financiera - 6to 'B'")
st.markdown("Plataforma abierta para la revisión y auditoría de fondos en tiempo real.")
st.markdown("---")

# 1. BLOQUE SUPERIOR DE INDICADORES (Métricas KPI)
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

#import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página - Acceso directo, público y optimizado para dispositivos móviles
st.set_page_config(
    page_title="Rendición de Cuentas - 6to B",
    page_icon="💰",
    layout="wide"
)

# --- FUNCIÓN PARA CARGAR DESDE GOOGLE SHEETS EN TIEMPO REAL ---
@st.cache_data(ttl=10)  # Actualiza la información cada 10 segundos de forma automática
def cargar_y_anonimizar_datos():
    # ID de tu enlace de Google Sheets compartido
    SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"
    SHEET_NAME = "NOMINA 6TO B" 
    
    # Construcción de la URL de exportación directa en formato CSV
    url_csv = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME.replace(' ', '%20')}"
    
    # 1. Lectura inicial en bruto tratando todo como string para evitar errores de tipo 'float'
    df_raw = pd.read_csv(url_csv, header=None, dtype=str).fillna("")
    
    # 2. Localización dinámica de la fila de encabezados de forma segura
    fila_header = 0
    for idx, row in df_raw.iterrows():
        # Pasamos toda la fila a mayúsculas y quitamos espacios residuales
        valores_fila = [str(val).upper().strip() for val in row.values]
        # Buscamos si en esta fila está la columna de estudiantes o los meses principales
        if any('NOMINA' in s or 'ESTUDIANTE' in s or 'MAY' in s for s in valores_fila):
            fila_header = idx
            break
            
    # 3. Re-procesamiento usando la fila correcta saltando encabezados institucionales superiores
    df = pd.read_csv(url_csv, skiprows=fila_header)
    
    # Renombrar la primera columna de forma estandarizada
    df.rename(columns={df.columns[0]: 'Estudiante'}, inplace=True)
    
    # Limpieza estricta de la nómina
    df = df[df['Estudiante'].notna()]
    df['Estudiante'] = df['Estudiante'].astype(str).str.strip()
    
    # Exclusión de las filas de totales inferiores del documento
    df = df[~df['Estudiante'].str.contains('TOTAL', case=False, na=False)]
    
    # FUNCIÓN DE PRIVACIDAD: Acortar nombres para acceso libre seguro en WhatsApp
    def simplificar_nombre(nombre_completo):
        partes = str(nombre_completo).split()
        if len(partes) >= 3:
            # Retorna: Primer Apellido + Primer Nombre
            return f"{partes[0]} {partes[2]}"
        elif len(partes) == 2:
            return f"{partes[0]} {partes[1]}"
        return nombre_completo

    df['Estudiante_Publico'] = df['Estudiante'].apply(simplificar_nombre)
    return df

# Control de carga y comunicación de fallas en la nube
try:
    df_ingresos = cargar_y_anonimizar_datos()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets en tiempo real: {e}")
    st.stop()

# --- REGISTRO DIRECTO DE GASTOS (EGRESOS) ---
# Puedes editar montos o añadir conceptos directamente en esta lista cuando gustes
gastos_data = {
    "Fecha": ["2026-05-10", "2026-05-15", "2026-06-02"],
    "Descripción / Concepto": ["Copias de exámenes de Matemáticas", "Cartelera para las fiestas patronales", "Agasajo del Día del Niño"],
    "Categoría": ["Material Académico", "Decoración", "Eventos"],
    "Monto ($)": [12.50, 25.00, 85.00]
}
df_gastos = pd.DataFrame(gastos_data)

# --- CÁLCULOS AUTOMÁTICOS DEL BALANCE DE CAJA ---
meses = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']

# Aseguramos la conversión de los datos de pagos a numéricos, reemplazando vacíos o textos por 0
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

# 2. PESTAÑAS DE NAVEGACIÓN INTERNA
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
    
    # Buscador optimizado y ordenado alfabéticamente
    estudiante_sel = st.selectbox("Seleccione el alumno:", sorted(df_ingresos['Estudiante_Publico'].unique()))
    datos_alumno = df_ingresos[df_ingresos['Estudiante_Publico'] == estudiante_sel]
    
    # Visualización de la fila de aportes del estudiante
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