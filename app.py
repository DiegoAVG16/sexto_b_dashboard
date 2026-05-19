import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
import time

# Configuración de la interfaz del dashboard
st.set_page_config(
    page_title="Transparencia Financiera - 6to B",
    page_icon="💰",
    layout="wide"
)

# Parámetros numéricos internos de pestaña (GIDs) oficiales de tu documento
GID_INGRESOS = "0"
GID_EGRESOS = "1460599602"  

# Mapeo posicional exacto para la pestaña de INGRESOS:
# Columna A (Estudiante) = Índice 0
# Columna B (MAY) = Índice 1, Columna C (JUN) = Índice 2, etc.
MAPEO_INGRESOS = {
    'MAY': 1, 'JUN': 2, 'JUL': 3, 'AGO': 4, 'SEP': 5,
    'OCT': 6, 'NOV': 7, 'DIC': 8, 'ENE': 9, 'FEB': 10
}

# Mapeo posicional exacto para la pestaña de EGRESOS:
# Columna A (OBS / Concepto) = Índice 0
# Columna B (MAYO) = Índice 1, Columna C (JUNIO) = Índice 2, etc.
MAPEO_EGRESOS = {
    'MAYO': 1, 'JUNIO': 2, 'JULIO': 3, 'AGOSTO': 4, 'SEPTIEMBRE': 5,
    'OCTUBRE': 6, 'NOVIEMBRE': 7, 'DICIEMBRE': 8, 'ENERO': 9, 'FEBRERO': 10
}

def descargar_csv(gid):
    """Descarga el CSV usando la URL de publicación real (2PACX) rompiendo la caché de red"""
    # El parámetro &t={int(time.time())} evita que Streamlit o el navegador devuelvan datos viejos en caché
    url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vQvB8RfFCeQKwZ9sT7tag7KSyOCVAakAZqAmVr4epUoHM0Pwv pUkc4AzoQm9Xnce5jXF9ojROOLUMv7/pub?output=csv&gid={gid}&t={int(time.time())}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text), header=None, dtype=str).fillna("0")
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def cargar_ingresos():
    df = descargar_csv(GID_INGRESOS)
    if df.empty or len(df) <= 2:
        return pd.DataFrame(columns=['Estudiante'] + list(MAPEO_INGRESOS.keys()) + ['Estudiante_Publico'])
        
    lista_ingresos = []
    # Fila 0: "NOMINA 6TO B", Fila 1: "MAY, JUN...", Fila 2: Datos reales de alumnos
    df_datos = df.iloc[2:].copy() 
    
    for _, fila in df_datos.iterrows():
        if len(fila) <= 1:
            continue
        nombre = str(fila.iloc[0]).strip()
        
        # Filtro de seguridad para ignorar encabezados repetidos o totales inferiores
        if nombre == "0" or nombre == "" or "TOTAL" in nombre.upper() or "NOMINA" in nombre.upper():
            continue
            
        registro = {'Estudiante': nombre}
        for mes_nombre, col_idx in MAPEO_INGRESOS.items():
            if col_idx < len(fila):
                valor = str(fila.iloc[col_idx]).replace('$', '').replace(',', '').strip()
                try:
                    registro[mes_nombre] = float(valor) if valor not in ["0", ""] else 0.0
                except ValueError:
                    registro[mes_nombre] = 0.0
            else:
                registro[mes_nombre] = 0.0
        lista_ingresos.append(registro)
        
    if not lista_ingresos:
        return pd.DataFrame(columns=['Estudiante'] + list(MAPEO_INGRESOS.keys()) + ['Estudiante_Publico'])
        
    df_res = pd.DataFrame(lista_ingresos)
    
    # Formateo público de nombres (Primer Nombre + Primer Apellido)
    def simplificar_nombre(n):
        partes = str(n).split()
        return f"{partes[0]} {partes[2]}" if len(partes) >= 3 else n
    df_res['Estudiante_Publico'] = df_res['Estudiante'].apply(simplificar_nombre)
    return df_res

def cargar_egresos():
    df = descargar_csv(GID_EGRESOS)
    df_vacio = pd.DataFrame(columns=["Concepto / Descripción", "Mes", "Monto ($)"])
    
    if df.empty or len(df) <= 1:
        return df_vacio
        
    lista_gastos = []
    df_datos = df.iloc[1:].copy() # Fila 0 es la cabecera de la hoja de egresos
    
    for _, fila in df_datos.iterrows():
        if fila.empty or pd.isna(fila.iloc[0]):
            continue
        concepto = str(fila.iloc[0]).strip()
        
        if concepto == "0" or concepto == "" or "TOTAL" in concepto.upper() or "OBS" in concepto.upper():
            continue
            
        for mes_nombre, col_idx in MAPEO_EGRESOS.items():
            if col_idx < len(fila):
                valor = str(fila.iloc[col_idx]).replace('$', '').replace(',', '').strip()
                try:
                    monto = float(valor) if valor not in ["0", ""] else 0.0
                except ValueError:
                    monto = 0.0
                    
                # Sangría e indentación corregidas de forma estricta para el bucle
                if monto > 0:
                    lista_gastos.append({
                        "Concepto / Descripción": concepto,
                        "Mes": mes_nombre.capitalize(),
                        "Monto ($)": monto
                    })
                    
    if not lista_gastos:
        return df_vacio
        
    return pd.DataFrame(lista_gastos)

# --- PROCESAMIENTO SEGURO DE DATOS ---
df_ingresos = cargar_ingresos()
df_gastos = cargar_egresos()

meses_cols = list(MAPEO_INGRESOS.keys())
for col in meses_cols:
    if col not in df_ingresos.columns:
        df_ingresos[col] = 0.0

# Operaciones de agregación