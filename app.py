import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from db import get_connection, init_db

# Page Configuration
st.set_page_config(page_title="Drop Item Map", layout="wide")

# Initialize Database on first run
# In a production app, this might be done differently, but for this simple app it ensures table exists.
init_db()

@st.cache_data(ttl=60)
def load_data(search_query=None):
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        if search_query:
            query = """
                SELECT id, title, description, latitude, longitude, created_at 
                FROM found_items 
                WHERE title ILIKE %s OR description ILIKE %s
                ORDER BY created_at DESC
            """
            like_query = f"%{search_query}%"
            cur.execute(query, (like_query, like_query))
        else:
            query = "SELECT id, title, description, latitude, longitude, created_at FROM found_items ORDER BY created_at DESC"
            cur.execute(query)
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

def insert_data(title, description, lat, lon):
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        query = "INSERT INTO found_items (title, description, latitude, longitude) VALUES (%s, %s, %s, %s)"
        cur.execute(query, (title, description, lat, lon))
        conn.commit()
        cur.close()
        conn.close()
        # Clear cache after insertion
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"Error inserting data: {e}")
        return False

# Sidebar - will be populated after map interaction to capture clicks
# but we need to initialize session state for inputs if they don't exist
if 'lat' not in st.session_state:
    st.session_state.lat = 35.6895
if 'lon' not in st.session_state:
    st.session_state.lon = 139.6917
if 'previous_click' not in st.session_state:
    st.session_state.previous_click = None

# Main Area
st.title("🗺️ 落とし物投稿・検索サイト (Lost & Found Map)")

# Search
search_term = st.text_input("🔍 検索 (Search by keyword)", "")

# Load Data
data = load_data(search_term)
df = pd.DataFrame(data, columns=["ID", "Title", "Description", "Latitude", "Longitude", "Created At"]) if data else pd.DataFrame()

# Session State for Map View
if 'map_center' not in st.session_state:
    st.session_state.map_center = [35.6895, 139.6917]
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 12
if 'last_selection' not in st.session_state:
    st.session_state.last_selection = []

# Handle Dataframe Selection
if "item_list" in st.session_state:
    selection = st.session_state.item_list.get("selection", {}).get("rows", [])
    if selection and selection != st.session_state.last_selection:
        # User selected a new row
        if not df.empty and selection[0] < len(df):
            selected_row = df.iloc[selection[0]]
            st.session_state.map_center = [selected_row["Latitude"], selected_row["Longitude"]]
            st.session_state.map_zoom = 16
            st.session_state.last_selection = selection
    elif not selection:
        st.session_state.last_selection = []

# Define Map Creation without Cache Resource (to avoid weird state loops)
def create_map(center, zoom, dataframe):
    m = folium.Map(location=center, zoom_start=zoom)
    if not dataframe.empty:
        for _, item in dataframe.iterrows():
            folium.Marker(
                [item["Latitude"], item["Longitude"]],
                popup=f"<b>{item['Title']}</b><br>{item['Description']}",
                tooltip=item['Title'],
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)
    return m

# Create Map
m = create_map(st.session_state.map_center, st.session_state.map_zoom, df)

# Render Map and Capture Click
# Return center/zoom to track pans
map_data = st_folium(m, width="100%", height=600, key="main_map", returned_objects=["last_clicked", "center", "zoom"])

# Update map state from manual interaction for NEXT run
# (This allows panning persistence across other interactions)
if map_data:
    if "center" in map_data and map_data["center"]:
         # We just update the session state. No rerun. 
         # The current map is already rendered.
         # Next time script runs (e.g. click form), it will use this new center.
         st.session_state.map_center = [map_data["center"]["lat"], map_data["center"]["lng"]]
    if "zoom" in map_data:
         st.session_state.map_zoom = map_data["zoom"]

# Handle Map Click
if map_data and map_data.get("last_clicked"):
    clicked = map_data["last_clicked"]
    if clicked != st.session_state.previous_click:
        st.session_state.lat = clicked["lat"]
        st.session_state.lon = clicked["lng"]
        st.session_state.previous_click = clicked

# Sidebar - Submission Form (Moved to bottom to access map_data)
st.sidebar.header("📝 投稿フォーム (Submit Item)")
with st.sidebar.form("entry_form", clear_on_submit=True):
    title = st.text_input("タイトル (Title)")
    desc = st.text_area("説明 (Description)")
    # Use session_state for values
    lat_input = st.number_input("緯度 (Latitude)", key="lat", format="%.6f")
    lon_input = st.number_input("経度 (Longitude)", key="lon", format="%.6f")
    
    submitted = st.form_submit_button("投稿する (Submit)")

    if submitted:
        if title and lat_input and lon_input:
            if insert_data(title, desc, lat_input, lon_input):
                st.sidebar.success("Submitted successfully!")
                st.session_state.previous_click = None 
                # Clear data cache
                load_data.clear()
                st.rerun() 
            else:
                st.sidebar.error("Failed to submit.")
        else:
            st.sidebar.warning("Title, Latitude, and Longitude are required.")

# Display Data as list below map
st.subheader("📦 投稿一覧 (Items List - Select row to view on map)")
if not df.empty:
    st.dataframe(
        df, 
        key="item_list",
        on_select="rerun",
        selection_mode="single-row"
    )
else:
    st.info("No items found.")
