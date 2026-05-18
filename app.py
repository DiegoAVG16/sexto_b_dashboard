import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página del dashboard
st.set_page_config(
    page_title="Rendición de Cuentas - 6to B",
    page_icon="💰",
    layout="wide"
)

# ID único de tu enlace compartido de Google Sheets
SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"

# --- FUNCIÓN AUTOMÁTICA PARA CARGAR INGRESOS (TABLA DE ALUMNOS) ---
@st.cache_data(ttl=5)
def cargar_ingresos():
    url_csv = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=INGRESOS"
    
    # Saltamos la primera fila vacía para capturar la fila con los meses correctamente
    df = pd.read_csv(url_csv, skiprows=1, dtype=str).fillna("0")
    
    # Aseguramos el nombre de la columna de nómina
    df.rename(columns={df.columns[0]: 'Estudiante'}, inplace=True)
    df['Estudiante'] = df['Estudiante'].astype(str).str.strip()
    
    # Filtrado estricto para limpiar cabeceras duplicadas o filas de totales inferiores
    df = df[df['Estudiante'].str.contains('[a-zA-Z]', na=False)]
    df = df[~df['Estudiante'].str.contains('TOTAL', case=False, na=False)]
    
    # Función de privacidad para acortar nombres en la vista pública
    def simplificar_nombre(nombre_completo):
        partes = str(nombre_completo).split()
        if len(partes) >= 3:
            return f"{partes[0]} {partes[2]}"
        elif len(partes) == 2:
            return f"{partes[0]} {partes[1]}"
        return nombre_completo

    df['Estudiante_Publico'] = df['Estudiante'].apply(simplificar_nombre)
    return df


# --- FUNCIÓN AUTOMÁTICA PARA CARGAR EGRESOS (TABLA DE GASTOS) ---
@st.cache_data(ttl=5)
def cargar_egresos():
    url_csv = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=EGRESOS"
    
    # Leemos la pestaña de Egresos directamente desde Google Sheets
    df_raw = pd.read_csv(url_csv, dtype=str).fillna("0")
    
    # Buscamos las columnas de meses en la hoja de egresos (MAYO, JUNIO, JULIO...)
    columnas_meses = [c for c in df_raw.columns if c.upper() != 'OBS']
    
    lista_gastos = []
    
    # Procesamos las filas para estructurar la tabla de gastos de forma legible
    for _, fila in df_raw.iterrows():
        concepto = str(fila['OBS']).strip()
        # Ignoramos filas vacías o decorativas en la hoja de cálculo
        if concepto == "0" or concepto == "" or "TOTAL" in concepto.upper():
            continue
            
        for mes in columnas_meses:
            valor_texto = str(fila[mes]).replace('$', '').replace(',', '').strip()
            try:
                monto = float(valor_texto)
            except ValueError:
                monto = 0.0
                
            if monto > 0:
                lista_gastos.append({
                    "Concepto / Descripción": concepto,
                    "Mes Correspondiente": mes.capitalize(),
                    "Monto ($)": monto
                })
                
    # Si la hoja está temporalmente vacía, generamos un DataFrame con la estructura correcta
    if not lista_gastos:
        return pd.DataFrame(columns=["Concepto / Descripción", "Mes Correspondiente", "Monto ($)"])
        
    return pd.DataFrame(lista_gastos)


# --- CONTROL DE CARGA SEGURO ---
try:
    df_ingresos = cargar_ingresos()
    df_gastos = cargar_egresos()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets en tiempo real: {e}")
    st.stop()


# --- MAPEO DINÁMICO DE APORTES MENSUALES (INGRESOS) ---
meses_ingresos = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']

for i, mes in enumerate(meses_ingresos):
    col_encontrada = [c for c in df_ingresos.columns if mes in str(c).upper()]
    if col_encontrada:
        df_ingresos[mes] = pd.to_numeric(df_ingresos[col_encontrada[0]], errors='coerce').fillna(0)
    elif i + 2 < len(df_ingresos.columns):
        df_ingresos[mes] = pd.to_numeric(df_ingresos.iloc[:, i + 2], errors='coerce').fillna(0)
    else:
        df_ingresos[mes] = 0.0


# --- CÁLCULOS GENERALES EN TIEMPO REAL ---
total_ingresos = df_ingresos[meses_ingresos].sum().sum()
total_gastos = df_gastos["Monto ($)"].sum() if not df_gastos.empty else 0.0
saldo_disponible = total_ingresos - total_gastos


# --- INTERFAZ GRÁFICA DEL DASHBOARD ---
st.title("📊 Transparencia Financiera - 6to 'B'")
st.markdown("Plataforma abierta para la revisión y auditoría de fondos de los padres de familia.")
st.markdown("---")

# 1. BLOQUE DE MÉTRICAS GENERALES DINÁMICAS
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
    
    st.dataframe(datos_alumno[['Estudiante_Publico'] + meses_ingresos], use_container_width=True)
    
    total_alumno = datos_alumno[meses_ingresos].sum(axis=1).values[0]
    st.success(f"El alumno seleccionado registra un aporte acumulado de: **${total_alumno:,.2f}**.")
    
    st.markdown("---")
    st.subheader("📈 Tendencia de Recaudación Mensual")
    ingresos_por_mes = df_ingresos[meses_ingresos].sum().reset_index()
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