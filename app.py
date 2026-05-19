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

# Mapeo estricto de columnas según la estructura de tus hojas
# Columna A = OBS/Nombres (Índice 0)
# Columna B = MAYO (Índice 1), Columna C = JUNIO (Índice 2), Columna D = JULIO (Índice 3)...
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

# --- FUNCIÓN: CARGAR INGRESOS (ALUMNOS) ---
@st.cache_data(ttl=5)
def cargar_ingresos():
    # Descarga de la primera pestaña usando gid=0 (INGRESOS)
    url_ingresos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
    df = pd.read_csv(url_ingresos, header=None, dtype=str).fillna("0")
    
    # Nos saltamos las dos primeras filas de títulos/cabeceras mixtas para ir a los alumnos
    df_datos = df.iloc[2:].copy()
    lista_ingresos = []
    
    for _, fila in df_datos.iterrows():
        nombre = str(fila.iloc[0]).strip()
        # Filtrar celdas vacías o filas de totales inferiores en la hoja
        if nombre == "0" or nombre == "" or "TOTAL" in nombre.upper():
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
    
    # Formato de nombre público para visualización rápida del aula
    def simplificar(n):
        p = str(n).split()
        return f"{p[0]} {p[2]}" if len(p) >= 3 else n
    df_res['Estudiante_Publico'] = df_res['Estudiante'].apply(simplificar)
    return df_res


# --- FUNCIÓN: CARGAR EGRESOS (GASTOS) ---
@st.cache_data(ttl=5)
def cargar_egresos():
    # Usamos gid=1460599602 o exportación directa por índice/nombre alternativo para evitar el Error 400
    # Si continúa el error 400, asegúrate de que la pestaña en tu Sheets se llame exactamente "EGRESOS"
    url_egresos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=EGRESOS"
    
    df = pd.read_csv(url_egresos, header=None, dtype=str).fillna("0")
    
    # La primera fila (índice 0) son las cabeceras (OBS, MAYO, JUNIO...)
    df_datos = df.iloc[1:].copy()
    lista_gastos = []
    
    for _, fila in df_datos.iterrows():
        concepto = str(fila.iloc[0]).strip()
        if concepto == "0" or concepto == "" or "TOTAL" in concepto.upper():
            continue
            
        # Recorremos cada mes buscando montos mayores a 0 en esa fila
        for mes_nombre, col_idx in MAPEO_MESES.items():
            if col_idx < len(fila):
                valor = str(fila.iloc[col_idx]).replace('$', '').replace(',', '').strip()
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
except Exception as e:
    st.error(f"Error al conectar con Google Sheets en tiempo real: {e}")
    st.info("💡 Consejo: Verifica que la pestaña de gastos se llame exactamente 'EGRESOS' en tu Google Sheets.")
    st.stop()

# Lista de columnas de meses para cálculos matemáticos
meses_cols = list(MAPEO_MESES.keys())

# Operación de suma total automatizada por Pandas
total_ingresos = df_ingresos[meses_cols].sum().sum()
total_gastos = df_gastos["Monto ($)"].sum() if not df_gastos.empty else 0.0
saldo_caja = total_ingresos - total_gastos


# --- DISEÑO DE LA INTERFAZ ---
st.title("📊 Transparencia Financiera - 6to 'B'")
st.markdown("Plataforma abierta para el control y rendición de cuentas del comité de padres.")
st.markdown("---")

# Tarjetas de totales
c1, c2, c3 = st.columns(3)
with c1:
    st.metric(label="🟢 Total Recaudado (Ingresos)", value=f"${total_ingresos:,.2f}")
with c2:
    st.metric(label="🔴 Total Invertido (Gastos)", value=f"${total_gastos:,.2f}")
with c3:
    st.metric(label="🔵 Saldo Neto Disponible", value=f"${saldo_caja:,.2f}")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Resumen de Caja", "🏦 Control de Ingresos", "📋 Detalle de Egresos"])

with tab1:
    st.subheader("Estado de Cuenta General")
    df_chart = pd.DataFrame({
        "Flujo": ["Ingresos", "Gastos"],
        "Valores ($)": [total_ingresos, total_gastos]
    })
    fig = px.bar(df_chart, x="Flujo", y="Valores ($)", color="Flujo", 
                 color_discrete_map={"Ingresos": "#2ecc71", "Gastos": "#e74c3c"}, text_auto='.2f')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("🔍 Consulta Individual de Aportes")
    if not df_ingresos.empty:
        selector = st.selectbox("Seleccione el nombre del estudiante:", sorted(df_ingresos['Estudiante_Publico'].unique()))
        filtro = df_ingresos[df_ingresos['Estudiante_Publico'] == selector]
        st.dataframe(filtro[['Estudiante_Publico'] + meses_cols], use_container_width=True)
        sum_individual = filtro[meses_cols].sum(axis=1).values[0]
        st.success(f"Aporte total acumulado de este estudiante: **${sum_individual:,.2f}**")

with tab3:
    st.subheader("📋 Listado Detallado de Gastos Realizados")
    if not df_gastos.empty:
        st.dataframe(df_gastos, use_container_width=True)
        fig_pie = px.pie(df_gastos, values='Monto ($)', names='Concepto / Descripción', title='Distribución del Gasto')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No se registran gastos para los meses evaluados actualmente.")