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

# --- IDENTIFICADORES DE PESTAÑA (GIDs) ---
# REVISIÓN CRUCIAL: Abre tu Google Sheets en el navegador, haz clic en la pestaña EGRESOS
# y mira el número que sale al final de la URL después de 'gid='. Cambia "1460599602" por ese número exacto.
GID_INGRESOS = "0"
GID_EGRESOS = "1460599602" 

# Mapeo posicional de columnas basado en tus capturas reales:
# Columna B (Índice 1) = Nombres de Alumnos / Conceptos Gastos
# Columna C (Índice 2) = MAYO, Columna D (Índice 3) = JUNIO, Columna E (Índice 4) = JULIO...
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

# --- FUNCIÓN: CARGAR INGRESOS (ALUMNOS) ---
@st.cache_data(ttl=2)
def cargar_ingresos():
    url_ingresos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID_INGRESOS}"
    df = pd.read_csv(url_ingresos, header=None, dtype=str).fillna("0")
    
    # Saltamos las primeras filas de encabezado desalineadas
    df_datos = df.iloc[2:].copy()
    lista_ingresos = []
    
    for _, fila in df_datos.iterrows():
        # En tu captura, los nombres están en la columna B (Índice 1)
        if len(fila) <= 1:
            continue
        nombre = str(fila.iloc[1]).strip()
        
        # Saltarse filas vacías, de diseño o la fila de totales (Fila 42 que suma 135, 10, etc.)
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
    
    # Simplificación de nombres para el selector público
    def simplificar(n):
        partes = str(n).split()
        return f"{partes[0]} {partes[2]}" if len(partes) >= 3 else n
    df_res['Estudiante_Publico'] = df_res['Estudiante'].apply(simplificar)
    return df_res


# --- FUNCIÓN: CARGAR EGRESOS (GASTOS) ---
@st.cache_data(ttl=2)
def cargar_egresos():
    # Usar el GID numérico directo elimina por completo el HTTP Error 400
    url_egresos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID_EGRESOS}"
    df = pd.read_csv(url_egresos, header=None, dtype=str).fillna("0")
    
    # Fila 0 contiene los meses (MAYO, JUNIO...). Empezamos a evaluar desde fila 1
    df_datos = df.iloc[1:].copy()
    lista_gastos = []
    
    for _, fila in df_datos.iterrows():
        # Concepto del gasto en la columna A (Índice 0) de la hoja EGRESOS
        concepto = str(fila.iloc[0]).strip()
        if concepto == "0" or concepto == "" or "TOTAL" in concepto.upper() or "OBS" in concepto.upper():
            continue
            
        # Cruzamos la matriz buscando montos asignados a cada mes en esa fila
        for mes_nombre, col_idx in MAPEO_MESES.items():
            # En la hoja egresos las columnas están recorridas un índice a la izquierda respecto a ingresos
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


# --- PROCESAMIENTO GENERAL ---
try:
    df_ingresos = cargar_ingresos()
    df_gastos = cargar_egresos()
    error_conexion = False
except Exception as e:
    error_conexion = True
    st.error(f"⚠️ Error de Comunicación con Google Sheets: {e}")
    st.info("💡 Solución rápida: Asegúrate de colocar el GID correcto de la pestaña EGRESOS en la línea 19 del código.")

if not error_conexion:
    meses_cols = list(MAPEO_MESES.keys())
    
    # Totales Dinámicos calculados por código puro de Python
    total_ingresos = df_ingresos[meses_cols].sum().sum()
    total_gastos = df_gastos["Monto ($)"].sum() if not df_gastos.empty else 0.0
    saldo_caja = total_ingresos - total_gastos

    # --- DISEÑO DEL DASHBOARD ---
    st.title("📊 Transparencia Financiera - 6to 'B'")
    st.markdown("Plataforma abierta para la revisión y auditoría de fondos en tiempo real.")
    st.markdown("---")

    # Bloques de Métricas Principales
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="🟢 Total Recaudado (Ingresos)", value=f"${total_ingresos:,.2f}")
    with c2:
        st.metric(label="🔴 Total Invertido (Gastos)", value=f"${total_gastos:,.2f}")
    with c3:
        st.metric(label="🔵 Saldo Neto Disponible en Caja", value=f"${saldo_caja:,.2f}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📉 Balance de Caja", "💰 Control de Aportes", "📋 Detalle de Gastos"])

    with tab1:
        st.subheader("Flujo de Efectivo Mensual")
        df_balance = pd.DataFrame({
            "Tipo": ["Ingresos Acumulados", "Gastos Acumulados"],
            "Monto ($)": [total_ingresos, total_gastos]
        })
        fig = px.bar(df_balance, x="Tipo", y="Monto ($)", color="Tipo",
                     color_discrete_map={"Ingresos Acumulados": "#2ecc71", "Gastos Acumulados": "#e74c3c"}, text_auto='.2f')
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("🔍 Buscador de Aportes por Estudiante")
        if not df_ingresos.empty:
            estudiante_sel = st.selectbox("Seleccione el alumno para verificar sus pagos:", sorted(df_ingresos['Estudiante_Publico'].unique()))
            filtro = df_ingresos[df_ingresos['Estudiante_Publico'] == estudiante_sel]
            st.dataframe(filtro[['Estudiante'] + meses_cols], use_container_width=True)
            
            total_estudiante = filtro[meses_cols].sum(axis=1).values[0]
            st.success(f"Aporte total entregado por el representante a la fecha: **${total_estudiante:,.2f}**")

    with tab3:
        st.subheader("📋 Cuentas Claras: Desglose de Egresos")
        if not df_gastos.empty:
            st.dataframe(df_gastos, use_container_width=True)
            fig_pie = px.pie(df_gastos, values='Monto ($)', names='Concepto / Descripción', title='¿Cómo se distribuyen los gastos del aula?')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No se registran egresos guardados en la hoja de Google Sheets actualmente.")