import xml.etree.ElementTree as ET
from datetime import datetime
import streamlit as st
import folium
import streamlit.components.v1 as components
import shapely.geometry as sg
import geopandas as gpd
import pandas as pd

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="La Conquista de los Cantones - La Palma",
    page_icon="🌋",
    layout="wide"
)

st.title("🌋 La Conquista de los Cantones Benahoaritas (La Palma)")
st.markdown("""
*Sistema de gamificación para el módulo de Organización de Itinerarios (OHI).*  
Los estudiantes reconquistan el territorio de la isla mediante sus rutas registradas en archivos GPX.
""")

# -----------------------------------------------------------------------------
# 2. DEFINICIÓN DE LOS 12 CANTONES BENAHOARITAS
# -----------------------------------------------------------------------------
def obtener_cantones_la_palma():
    """Retorna un GeoDataFrame con los 12 cantones históricos de La Palma."""
    cantones_data = [
        {"canton": "Tagalgen", "municipio": "Garafía", "geometry": sg.box(-17.95, 28.78, -17.85, 28.85)},
        {"canton": "Tagaragre", "municipio": "Barlovento", "geometry": sg.box(-17.85, 28.78, -17.78, 28.84)},
        {"canton": "Adeyahamen", "municipio": "San Andrés y Sauces", "geometry": sg.box(-17.82, 28.70, -17.74, 28.78)},
        {"canton": "Tenagua", "municipio": "Puntallana", "geometry": sg.box(-17.79, 28.65, -17.72, 28.72)},
        {"canton": "Tedote", "municipio": "Santa Cruz / Breñas", "geometry": sg.box(-17.82, 28.58, -17.74, 28.68)},
        {"canton": "Tigalate", "municipio": "Mazo", "geometry": sg.box(-17.84, 28.50, -17.75, 28.60)},
        {"canton": "Ahenguareme", "municipio": "Fuencaliente Sur", "geometry": sg.box(-17.86, 28.44, -17.80, 28.53)},
        {"canton": "Guehevey", "municipio": "Las Manchas / Tamanca", "geometry": sg.box(-17.90, 28.53, -17.82, 28.60)},
        {"canton": "Tahuya", "municipio": "El Paso / Los Llanos Sur", "geometry": sg.box(-17.92, 28.58, -17.84, 28.65)},
        {"canton": "Aridane", "municipio": "Los Llanos / Tazacorte", "geometry": sg.box(-17.96, 28.62, -17.88, 28.68)},
        {"canton": "Tijarafe", "municipio": "Tijarafe / Puntagorda", "geometry": sg.box(-17.98, 28.68, -17.88, 28.78)},
        {"canton": "Aceró", "municipio": "Caldera de Taburiente", "geometry": sg.box(-17.88, 28.66, -17.81, 28.75)},
    ]
    return gpd.GeoDataFrame(cantones_data, crs="EPSG:4326")

# -----------------------------------------------------------------------------
# 3. PROCESAMIENTO DE ARCHIVOS GPX
# -----------------------------------------------------------------------------
def procesar_gpx_subido(archivo_gpx, max_dist_cierre_m=100.0, franja_m=30.0):
    """Parsea el GPX y retorna la geometría proyectada a UTM Zona 28N (Canarias)."""
    tree = ET.parse(archivo_gpx)
    root = tree.getroot()
    puntos = []
    
    for elem in root.iter():
        if elem.tag.endswith('trkpt'):
            lat = float(elem.attrib['lat'])
            lon = float(elem.attrib['lon'])
            puntos.append((lon, lat))
            
    if len(puntos) < 3:
        return None, "Error: GPX con puntos insuficientes"
        
    linea = sg.LineString(puntos)
    gdf_linea = gpd.GeoDataFrame(geometry=[linea], crs="EPSG:4326").to_crs("EPSG:32628")
    geom_utm = gdf_linea.geometry.iloc[0]
    
    p_inicio = sg.Point(geom_utm.coords[0])
    p_fin = sg.Point(geom_utm.coords[-1])
    
    if p_inicio.distance(p_fin) <= max_dist_cierre_m:
        poligono = sg.Polygon(geom_utm.coords)
        if not poligono.is_valid:
            poligono = poligono.buffer(0)
        geom_conquista = poligono.buffer(5.0)
        tipo = "Ruta Circular (Conquista Interior)"
    else:
        geom_conquista = geom_utm.buffer(franja_m)
        tipo = f"Ruta Lineal (Franja {int(franja_m)}m)"
        
    return geom_conquista, tipo

# -----------------------------------------------------------------------------
# 4. ESTADO DE LA SESIÓN Y COLORES
# -----------------------------------------------------------------------------
if 'actividades' not in st.session_state:
    st.session_state.actividades = []

COLORES_ALUMNOS = [
    "#FF3333", "#3388FF", "#28A745", "#FFC107", "#9C27B0",
    "#FF5722", "#00BCD4", "#E91E63", "#4CAF50", "#673AB7"
]

# -----------------------------------------------------------------------------
# 5. PANEL LATERAL: CARGA DE RUTAS
# -----------------------------------------------------------------------------
st.sidebar.header("📤 Panel del Docente: Cargar GPX")

nombre_alumno = st.sidebar.text_input("Nombre del Alumno/a", value="Alumno 1")
fecha_ruta = st.sidebar.date_input("Fecha de la Ruta", value=datetime.now())
hora_ruta = st.sidebar.time_input("Hora de la Ruta", value=datetime.now().time())
archivo_gpx = st.sidebar.file_uploader("Subir archivo .gpx", type=["gpx"])

if st.sidebar.button("➕ Registrar Ruta y Actualizar Cantones"):
    if archivo_gpx is not None and nombre_alumno.strip():
        fecha_completa = datetime.combine(fecha_ruta, hora_ruta)
        geom, tipo = procesar_gpx_subido(archivo_gpx)
        
        if geom is not None:
            st.session_state.actividades.append({
                'alumno': nombre_alumno.strip(),
                'fecha': fecha_completa,
                'geometria_utm': geom,
                'tipo': tipo,
                'archivo': archivo_gpx.name
            })
            st.session_state.actividades.sort(key=lambda x: x['fecha'])
            st.sidebar.success(f"¡Ruta de {nombre_alumno} registrada con éxito ({tipo})!")
        else:
            st.sidebar.error("El archivo GPX no contiene datos de track válidos.")
    else:
        st.sidebar.warning("Introduce el nombre del alumno y selecciona un archivo GPX.")

# -----------------------------------------------------------------------------
# 6. CÁLCULO DE SOLAPAMIENTO Y RE-CONQUISTA
# -----------------------------------------------------------------------------
def calcular_dominios_actuales():
    dominios = {}
    for act in st.session_state.actividades:
        alumno = act['alumno']
        nueva_geom = act['geometria_utm']
        
        for al in list(dominios.keys()):
            if dominios[al] is not None and not dominios[al].is_empty:
                dominios[al] = dominios[al].difference(nueva_geom)
                
        if alumno not in dominios or dominios[alumno] is None or dominios[alumno].is_empty:
            dominios[alumno] = nueva_geom
        else:
            dominios[alumno] = dominios[alumno].union(nueva_geom)
            
    return dominios

dominios_utm = calcular_dominios_actuales()
alumnos_unicos = list(set([act['alumno'] for act in st.session_state.actividades]))
mapa_colores = {al: COLORES_ALUMNOS[i % len(COLORES_ALUMNOS)] for i, al in enumerate(alumnos_unicos)}

# -----------------------------------------------------------------------------
# 7. INTERFAZ WEB PRINCIPAL
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de la Conquista", "🏆 Ranking y Dominancia", "📜 Historial de Rutas"])

with tab1:
    st.subheader("Mapa en Vivo de La Palma")
    m = folium.Map(location=[28.65, -17.86], zoom_start=11, tiles="OpenStreetMap")
    
    cantones_gdf = obtener_cantones_la_palma()
    for _, row in cantones_gdf.iterrows():
        folium.GeoJson(
            sg.mapping(row['geometry']),
            style_function=lambda x: {'fillColor': '#f4a261', 'color': '#e76f51', 'weight': 1.5, 'fillOpacity': 0.15},
            tooltip=f"<b>Cantón:</b> {row['canton']}<br><b>Zona:</b> {row['municipio']}"
        ).add_to(m)
        
    for alumno, geom in dominios_utm.items():
        if geom is not None and not geom.is_empty:
            gdf_m = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:32628").to_crs("EPSG:4326")
            geom_wgs = gdf_m.geometry.iloc[0]
            area_m2 = geom.area
            color = mapa_colores.get(alumno, "#3388FF")
            
            folium.GeoJson(
                sg.mapping(geom_wgs),
                style_function=lambda x, col=color: {'fillColor': col, 'color': col, 'weight': 2, 'fillOpacity': 0.6},
                tooltip=f"<b>Dominio de:</b> {alumno}<br><b>Superficie:</b> {round(area_m2/10000, 2)} ha ({round(area_m2/1000000, 3)} km²)"
            ).add_to(m)
            
    components.html(m._repr_html_(), height=600)

with tab2:
    st.subheader("🏆 Clasificación General de Conquistadores")
    ranking_data = []
    for alumno, geom in dominios_utm.items():
        area_m2 = geom.area if (geom is not None and not geom.is_empty) else 0.0
        ranking_data.append({
            "Alumno/a": alumno,
            "Superficie (km²)": round(area_m2 / 1_000_000.0, 4),
            "Superficie (Hectáreas)": round(area_m2 / 10_000.0, 2),
            "Superficie (m²)": round(area_m2, 2)
        })
        
    if ranking_data:
        df_ranking = pd.DataFrame(ranking_data).sort_values(by="Superficie (m²)", ascending=False)
        df_ranking.index = range(1, len(df_ranking) + 1)
        st.dataframe(df_ranking, use_container_width=True)
    else:
        st.info("Aún no se han registrado rutas. Utiliza el panel lateral para subir los primeros archivos GPX.")

with tab3:
    st.subheader("📜 Registro de Actividades GPX Cargadas")
    if st.session_state.actividades:
        historial = [{
            "Fecha/Hora": act['fecha'].strftime("%Y-%m-%d %H:%M"),
            "Alumno/a": act['alumno'],
            "Tipo de Ruta": act['tipo'],
            "Archivo GPX": act['archivo']
        } for act in st.session_state.actividades]
        st.table(pd.DataFrame(historial))
    else:
        st.info("Sin actividades registradas.")
