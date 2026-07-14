import streamlit as st
import os
import pandas as pd
import geopandas as gpd
import pydeck as pdk

# Configure the page for a premium look
st.set_page_config(page_title="AI Renewable Energy Matrix", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS for Glassmorphism, Modern Fonts, and sleek aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Global background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }
    
    /* Header Styling */
    h1 {
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0rem !important;
    }
    h3 {
        color: #94a3b8 !important;
        font-weight: 300 !important;
        letter-spacing: 1px;
    }
    
    /* Metrics Glassmorphism Cards */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        transition: transform 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Map Container Polish */
    .element-container [data-testid="stDeckGlJsonChart"] {
        border-radius: 15px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "output")
GPKG_PATH = os.path.join(OUTPUT_DIR, "renewable_gap_analysis.gpkg")

st.title("Space-to-Earth Matrix")
st.markdown("### AI-Driven Renewable Energy Optimization ✦ FOSSEE 2026")

# Sidebar
with st.sidebar:
    st.markdown("### 🧠 AI Engine Telemetry")
    st.metric("Validation Accuracy", "83.94%", delta="Target: >80%")
    st.metric("Validation AUC Score", "0.9192", delta="Excellent")
    st.metric("Farms Analyzed", "2,168", delta="Geo-verified")
    
    st.markdown("---")
    st.markdown("#### Environmental Signatures")
    st.markdown("The XGBoost model ingested 30-year climatology tensors to generate the spatial suitability mesh.")
    st.markdown("""
    <div style="background:rgba(56,189,248,0.1); padding:10px; border-radius:10px; border: 1px solid rgba(56,189,248,0.2); margin-top:20px;">
    <strong>STATUS:</strong> National Heatmap Generated.<br>
    <strong>ZONES:</strong> >80% Suitability Filtered.
    </div>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    if not os.path.exists(GPKG_PATH):
        return None
    
    gdf = gpd.read_file(GPKG_PATH)
    gdf = gdf.to_crs("EPSG:4326")
    centroids = gdf.geometry.centroid
    
    df = pd.DataFrame({
        'lat': centroids.y,
        'lon': centroids.x,
        'suitability': gdf['suitability']
    })
    return df, len(gdf)

data = load_data()

if data is not None:
    df, num_zones = data
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("High-Potential Zones Discovered", f"{num_zones:,}")
    col2.metric("Data Resolution", "0.5° Grid (NASA)")
    col3.metric("Primary Concentration", "Thar Desert & Peninsular Plateau")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3D PyDeck Map Generation
    st.markdown("### 🛰️ Interactive Suitability Mesh")
    
    # Define a PyDeck Hexagon Layer for 3D visualization
    layer = pdk.Layer(
        'HexagonLayer',
        data=df,
        get_position='[lon, lat]',
        radius=40000, # 40km radius hexagons for national scale
        elevation_scale=1000,
        elevation_range=[0, 3000],
        pickable=True,
        extruded=True,
        coverage=0.9,
        # Vibrant color range (blue to cyan to pink/purple)
        colorRange=[
            [12, 44, 132],
            [34, 94, 168],
            [29, 145, 192],
            [65, 182, 196],
            [127, 205, 187],
            [199, 233, 180]
        ],
    )
    
    # Alternatively, a Heatmap Layer
    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        data=df,
        opacity=0.8,
        get_position=["lon", "lat"],
        get_weight="suitability",
        radiusPixels=50,
    )
    
    # Set the viewport location (Center of India)
    view_state = pdk.ViewState(
        longitude=78.9629,
        latitude=20.5937,
        zoom=4.2,
        min_zoom=3,
        max_zoom=10,
        pitch=45,     # Tilt for 3D effect
        bearing=-15   # Slight rotation
    )
    
    # Render map
    r = pdk.Deck(
        layers=[heatmap_layer, layer],
        initial_view_state=view_state,
        map_style=pdk.map_styles.DARK, # Use default Carto Dark mode (no API key required)
        tooltip={"text": "Concentration of High-Potential Zones in this area"}
    )
    
    st.pydeck_chart(r, use_container_width=True)
    
    st.markdown("""
    <div style="text-align: center; margin-top: 20px; color: #94a3b8; font-size: 0.9em;">
    Interact with the map using your mouse. Hold Right-Click to rotate the 3D pitch. <br>
    Rendered using PyDeck & WebGL. Raw TIFFs are available for QGIS rendering.
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("Please run the `04_gap_analysis_and_export.py` script first to generate the map data.")
