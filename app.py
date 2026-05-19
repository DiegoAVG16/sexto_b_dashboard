import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la interfaz del dashboard
st.set_page_config(
    page_title="Transparencia Financiera - 6to B",
    page_icon="💰",
    layout="wide"
)

# Identificador único de la hoja de cálculo en Google Drive
SPREADSHEET_ID = "1VbIg_GdnA9NFpgECH0SCHgqhCUsDmHVu0d5r-RJxnJY"

# Parámetros numéricos internos de pestaña (GIDs) obligatorios para evitar HTTP Error 400
GID_INGRESOS = "0"
GID_EGRESOS = "1460599602"  # Este ID numérico garantiza la descarga directa sin rechazos

# Mapeo de columnas correspondientes a los meses del año lectivo
MAPEO_MESES = {
    'MAYO': 2,
    'JUNIO': 3,
    'JULIO': 4,
    'AGOSTO': 5,
    'SEPTIEMBRE': 6,
    'OCTUBRE': 7,
    'NOVIEMBRE': 8,
    'DICIEMBRE': 9,
    'ENERO': 10,
    'FEBRERO': 11
}

@st.cache_data(ttl=2)
def cargar_ingresos():
    url_ingresos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID_INGRESOS}"
    df = pd.read_csv(url_ingresos, header=None, dtype=str).fillna("0")
    
    df_datos = df.iloc[2:].copy()
    lista_ingresos = []
    
    for _, fila in df_datos.iterrows():
        if len(fila) <= 1:
            continue
        nombre = str(fila.iloc[1]).strip()
        
        # Filtro para omitir celdas de totales o vacías en la nómina
        if nombre == "0" or nombre == "" or "TOTAL" in nombre.upper() or "INGRESOS" in nombre.upper():
            continue
            
        registro = {'Estudiante': nombre}
        for mes_nombre, col_idx in MAPEO_MESES.items():
            if col_idx < len(fila):
                valor = str(fila.iloc[col_idx]).replace('$', '').replace(',', '').strip()
                try:
                    registro[mes_nombre] = float(valor)
                except ValueError:
                    registro[mes_nombre] = 0.0
            else:
                registro[mes_nombre] = 0.0
        lista_ingresos.append(registro)
        
    if not lista_ingresos:
        return pd.DataFrame(columns=['Estudiante'] + list(MAPEO_MESES.keys()))
        
    df_res = pd.DataFrame(lista_ingresos)
    
    # Formateo de nombres para visualización en el buscador público
    def simplificar_nombre(n):
        partes = str(n).split()
        return f"{partes[0]} {partes[2]}" if len(partes) >= 3 else n
        
    df_res['Estudiante_Publico'] = df_res['Estudiante'].apply(simplificar_nombre)
    return df_res

@st.cache_data(ttl=2)
def cargar_egresos():
    # La consulta explícita por gid elimina de raíz el error de conexión Bad Request
    url_egresos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID_EGRESOS}"
    df = pd.read_csv(url_egresos, header=None, dtype=str).fillna("0")
    
    df_datos = df.iloc[1:].copy()
    lista_gastos = []
    
    for _, fila in df_datos.iterrows():
        concepto = str(fila.iloc[0]).strip()
        
        # Evita procesar filas vacías o descriptores de cabeceras
        if concepto == "0" or concepto == "" or "TOTAL" in concepto.upper() or "OBS" in concepto.upper():
            continue
            
        for mes_nombre, col_idx in MAPEO_MESES.items():
            # Desplazamiento posicional por diferencia de estructura en columnas de egresos
            idx_gasto = col_idx - 1 
            if idx_gasto < len(fila):
                valor = str(fila.iloc[idx_gasto]).replace('$', '').replace(',', '').strip()
                try:
                    monto = float(valor)
                except ValueError:
                    monto = 0.0
                    
                if monto > 0:
                    lista_gastos.append({
                        "Concepto / Descripción": concepto,
                        "Mes": mes_nombre.capitalize(),
                        "Monto ($)": monto
                    })
                    
    if not lista_gastos:
        return pd.DataFrame(columns=["Concepto / Descripción", "Mes", "Monto ($)"])
        
    return pd.DataFrame(lista_gastos)

# Flujo lógico de procesamiento e renderizado de la interfaz
try:
    df_ingresos = cargar_ingresos()
    df_gastos = cargar_egresos()
    error_conexion = False
except Exception as e:
    error_conexion = True
    st.error(f"⚠️ Error de Comunicación con Google Sheets: {e}")
    st.info("Asegúrese de validar que el ID de la hoja de cálculo y el GID asignado sigan siendo válidos y públicos.")

if not error_conexion:
    meses_cols = list(MAPEO_MESES.keys())
    
    # Cálculos internos de saldos y agregaciones
    total_ingresos = df_ingresos[meses_cols].sum().sum()
    total_gastos = df_gastos["Monto ($)"].sum() if not df_gastos.empty else 0.0
    saldo_caja = total_ingresos - total_gastos

    st.title("📊 Transparencia Financiera - 6to 'B'")
    st.markdown("Plataforma abierta para la revisión y auditoría de fondos de los padres de familia.")
    st.markdown("---")

    # Fila de indicadores financieros clave
    col_inc_1, col_inc_2, col_inc_3 = st.columns(3)
    with col_inc_1:
        st.metric(label="🟢 Total Recaudado (Ingresos)", value=f"${total_ingresos:,.2f}")
    with col_inc_2:
        st.metric(label="🔴 Total Invertido (Gastos)", value=f"${total_gastos:,.2f}")
    with col_inc_3:
        st.metric(label="🔵 Saldo Neto Disponible en Caja", value=f"${saldo_caja:,.2f}")

    st.markdown("---")

    pestaña_balance, pestaña_aportes, pestaña_egresos = st.tabs(["📉 Balance de Caja", "💰 Control de Aportes", "📋 Detalle de Gastos"])

    with pestaña_balance:
        st.subheader("Flujo de Efectivo Mensual")
        df_balance = pd.DataFrame({
            "Tipo": ["Ingresos Acumulados", "Gastos Acumulados"],
            "Monto ($)": [total_ingresos, total_gastos]
        })
        fig_balance = px.bar(
            df_balance, 
            x="Tipo", 
            y="Monto ($)", 
            color="Tipo",
            color_discrete_map={"Ingresos Acumulados": "#2ecc71", "Gastos Acumulados": "#e74c3c"}, 
            text_auto='.2f'
        )
        st.plotly_chart(fig_balance, use_container_width=True)

    with pestaña_aportes:
        st.subheader("🔍 Buscador de Aportes por Estudiante")
        if not df_ingresos.empty:
            estudiante_sel = st.selectbox("Seleccione el alumno para verificar sus pagos:", sorted(df_ingresos['Estudiante_Publico'].unique()))
            filtro = df_ingresos[df_ingresos['Estudiante_Publico'] == estudiante_sel]
            st.dataframe(filtro[['Estudiante'] + meses_cols], use_container_width=True)
            
            total_estudiante = filtro[meses_cols].sum(axis=1).values[0]
            st.success(f"Aporte total entregado por el representante a la fecha: **${total_estudiante:,.2f}**")

    with pestaña_egresos:
        st.subheader("📋 Cuentas Claras: Desglose de Egresos")
        if not df_gastos.empty:
            st.dataframe(df_gastos, use_container_width=True)
            fig_pie = px.pie(df_gastos, values='Monto ($)', names='Concepto / Descripción', title='¿Cómo se distribuyen los gastos del aula?')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No se registran egresos guardados en la hoja de Google Sheets actualmente.")