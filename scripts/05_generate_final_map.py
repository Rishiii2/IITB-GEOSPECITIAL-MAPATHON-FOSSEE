import os
import rasterio
from rasterio.plot import show
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.patches as mpatches

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "output")
HEATMAP_TIF = os.path.join(OUTPUT_DIR, "india_suitability_heatmap.tif")
VECTOR_GPKG = os.path.join(OUTPUT_DIR, "renewable_gap_analysis.gpkg")
FINAL_MAP_PDF = os.path.join(OUTPUT_DIR, "Final_Renewable_Energy_Map.pdf")
FINAL_MAP_PNG = os.path.join(OUTPUT_DIR, "Final_Renewable_Energy_Map.png")

print("Loading Data for Final Cartography...")
# Configure the plot with a dark theme for a premium look
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(12, 12), dpi=300)

# 1. Load and plot the Heatmap
print("Rendering Heatmap...")
with rasterio.open(HEATMAP_TIF) as src:
    heatmap_data = src.read(1)
    # Mask out the -9999 nodata values
    import numpy as np
    heatmap_data = np.where(heatmap_data == -9999.0, np.nan, heatmap_data)
    
    # Plot using a stunning 'magma' color map
    img = ax.imshow(heatmap_data, cmap='magma', extent=(
        src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top
    ))

# 2. Add the Colorbar (Legend)
cbar = fig.colorbar(img, ax=ax, shrink=0.5, orientation='vertical', pad=0.04)
cbar.set_label('AI Suitability Score', rotation=270, labelpad=20, fontsize=12, color='white')
cbar.ax.yaxis.set_tick_params(color='white')
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

# 3. Load and plot the High-Potential Polygons
print("Rendering Vector Polygons...")
if os.path.exists(VECTOR_GPKG):
    gdf = gpd.read_file(VECTOR_GPKG)
    # Plot with a neon cyan outline
    gdf.plot(ax=ax, facecolor='none', edgecolor='#00FFFF', linewidth=1.5)

# 4. Add Title and Formatting
print("Applying professional formatting...")
ax.set_title("Optimal Renewable Energy Zones in India\n(AI Multi-Criteria Spatial Analysis)", 
             fontsize=16, color='white', pad=20, fontweight='bold')
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

# Clean up axes colors
ax.spines['bottom'].set_color('white')
ax.spines['top'].set_color('white')
ax.spines['left'].set_color('white')
ax.spines['right'].set_color('white')
ax.tick_params(axis='x', colors='white')
ax.tick_params(axis='y', colors='white')

# Add FOSSEE Mapathon required participant details
text_box = "Participant: Rishikant\\nEmail: rishi.space2@gmail.com\\nFOSSEE Mapathon 2026"
props = dict(boxstyle='round', facecolor='#0f172a', alpha=0.8, edgecolor='#38bdf8')
ax.text(0.02, 0.03, text_box, transform=ax.transAxes, fontsize=10, color='white',
        verticalalignment='bottom', bbox=props)

# 5. Export to High-Res PDF and PNG
print("Exporting Final Maps...")
plt.savefig(FINAL_MAP_PDF, format='pdf', bbox_inches='tight', facecolor='#0f172a')
plt.savefig(FINAL_MAP_PNG, format='png', bbox_inches='tight', facecolor='#0f172a')
plt.close()

print(f"Success! Final maps saved to:\\n- {FINAL_MAP_PDF}\\n- {FINAL_MAP_PNG}")
