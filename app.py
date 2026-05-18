import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página del dashboard
st.set_page_config(
    page_title="Rendición de Cuentas - 6to B",
    page_icon="💰",
    layout="wide"
)

# ID de tu documento de Google Sheets
SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"

# --- FUNCIÓN PARA CARGAR INGRESOS (HOJA 1) ---
@st.cache_data(ttl=3)
def cargar_ingresos():
    # Usamos el formato de exportación directa por GID para asegurar que no se crucen las hojas
    # gid=0 suele corresponder a la primera pestaña (INGRESOS)
    url_ingresos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
    
    # Saltamos la primera fila vacía para que la fila con los meses (MAY, JUN...) sea la cabecera real
    df = pd.read_csv(url_ingresos, skiprows=1, dtype=str).fillna("0")
    
    # Aseguramos el nombre de la columna de la nómina
    df.rename(columns={df.columns[0]: 'Estudiante'}, inplace=True)
    df['Estudiante'] = df['Estudiante'].astype(str).str.strip()
    
    # Filtrado estricto para limpiar cabeceras vacías o filas de totales inferiores
    df = df[df['Estudiante'].str.contains('[a-zA-Z]', na=False)]
    df = df[~df['Estudiante'].str.contains('TOTAL', case=False, na=False)]
    
    # Privacidad de nombres en la web pública
    def simplificar_nombre(nombre_completo):
        partes = str(nombre_completo).split()
        if len(partes) >= 3:
            return f"{partes[0]} {partes[2]}"
        elif len(partes) == 2:
            return f"{partes[0]} {partes[1]}"
        return nombre_completo

    df['Estudiante_Publico'] = df['Estudiante'].apply(simplificar_nombre)
    return df


# --- FUNCIÓN PARA CARGAR EGRESOS (HOJA 2) ---
@st.cache_data(ttl=3)
def cargar_egresos():
    # Usamos la API de visualización estructurada apuntando directamente a la hoja EGRESOS
    url_csv = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=EGRESOS"
    
    df_raw = pd.read_csv(url_csv, dtype=str).fillna("0")
    
    # Aseguramos limpiar los nombres de las columnas
    df_raw.columns = [str(c).strip().upper() for c in df_raw.columns]
    
    lista_gastos = []
    
    # Buscamos las columnas de meses disponibles en la hoja de egresos
    columnas_meses = [c for c in df_raw.columns if c != 'OBS' and not c.startswith('UNNAMED')]
    
    for _, fila in df_raw.iterrows():
        concepto = str(fila.get('OBS', '')).strip()
        if concepto == "0" or concepto == "" or "TOTAL" in concepto.upper():
            continue
            
        for mes in columnas_meses:
            valor_texto = str(fila.get(mes, '0')).replace('$', '').replace(',', '').strip()
            try:
                monto = float(valor_texto)
            except ValueError:
                monto = 0.0
                
            if monto > 0:
                lista_gastos.append({
                    "Concepto / Descripción": concepto,
                    "Mes": mes.capitalize(),
                    "Monto ($)": monto
                })
                
    if not lista_gastos:
        return pd.DataFrame(columns=["Concepto / Descripción", "Mes", "Monto ($)"])
        
    return pd.DataFrame(lista_gastos)


# --- EJECUCIÓN SEGURA DE LA CARGA ---
try:
    df_ingresos = cargar_ingresos()
    df_gastos = cargar_egresos()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.stop()


# --- PROCESAMIENTO MENSÚAL DE INGRESOS ---
meses_ingresos = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB']

for i, mes in enumerate(meses_ingresos):
    col_encontrada = [c for c in df_ingresos.columns if mes in str(c).upper()]
    if col_encontrada:
        df_ingresos[mes] = pd.to_numeric(df_ingresos[col_encontrada[0]], errors='coerce').fillna(0)
    elif i + 2 < len(df_ingresos.columns):
        df_ingresos[mes] = pd.to_numeric(df_ingresos.iloc[:, i + 2], errors='coerce').fillna(0)
    else:
        df_ingresos[mes] = 0.0


# --- CÁLCULOS FILTRADOS FINALES ---
total_ingresos = df_ingresos[meses_ingresos].sum().sum()
total_gastos = df_gastos["Monto ($)"].sum() if not df_gastos.empty else 0.0
saldo_disponible = total_ingresos - total_gastos


# --- INTERFAZ GRÁFICA DEL DASHBOARD ---
st.title("📊 Transparencia Financiera - 6to 'B'")
st.markdown("Plataforma abierta para la revisión y auditoría de fondos de los padres de familia.")
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

# 2. PESTAÑAS DE INFORMACIÓN
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