# admin.py

import streamlit as st
from admin.simulation_handler import orchestrate_simulation_workflow, get_available_simulations, load_simulation_summary
from admin.upload_handler import upload_projection_file
from app.dataviz import load_visualizations
import logging
import os
from io import BytesIO
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_df_to_csv(df: pd.DataFrame) -> BytesIO:
    """
    Converts a DataFrame to a CSV bytes buffer.

    Args:
        df (pd.DataFrame): DataFrame to convert.

    Returns:
        BytesIO: Bytes buffer containing CSV data.
    """
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer

def main():
    st.set_page_config(page_title="NFL Simulator - Admin Panel", layout="wide")
    st.title("🏈 NFL Simulator - Admin Panel")

    # Placeholder for status messages
    status_placeholder = st.empty()

    # Sidebar for simulation trigger
    st.sidebar.header("🔄 Run Simulations")
    num_simulations = st.sidebar.number_input(
        "Number of Simulations", 
        min_value=10, 
        max_value=10000, 
        value=1000, 
        step=10
    )
    
    # Sidebar for uploading projections
    st.sidebar.header("📤 Upload Projections")
    uploaded_file = st.sidebar.file_uploader("Upload a projection CSV file", type=['csv'])
    if uploaded_file is not None:
        try:
            # Upload and save the projection file
            saved_path = upload_projection_file(uploaded_file)
            status_placeholder.success(f"✅ Uploaded projection file: {uploaded_file.name}")
        except Exception as e:
            status_placeholder.error(f"❌ Failed to upload projection file: {e}")
            logger.error(f"Failed to upload projection file: {e}")

    # Sidebar selection for projection source
    projection_choice = st.sidebar.selectbox(
        "Select Projection Source",
        options=["Default Projections", "User Uploaded Projections"]
    )
    if projection_choice == "Default Projections":
        projection_path = 'data/raw/'  # Changed from 'data/projections/default/'
    else:
        projection_path = 'data/projections/user_uploads/'
        if not os.listdir(projection_path):
            st.sidebar.error("❌ No user-uploaded projection files found.")
            projection_path = 'data/raw/'  # Fallback to raw data if user uploads are missing

    # Button to run simulation
    if st.sidebar.button("🚀 Run Simulation"):
        with st.spinner("🕒 Running simulations..."):
            try:
                summary = orchestrate_simulation_workflow(num_simulations, projection_path=projection_path)
                status_placeholder.success("✅ Simulations completed successfully!")
            except Exception as e:
                status_placeholder.error(f"❌ An error occurred during the simulation: {e}")
                logger.error(f"Simulation error: {e}")
                return

        if summary is not None:
            # Display total games
            st.subheader("📊 Total Games Simulated")
            st.write(summary.get('total_games', 'N/A'))
            logger.info("Displayed total games simulated.")
            
            # Load and execute all visualizations
            visualizations = load_visualizations()
            if not visualizations:
                st.warning("⚠️ No visualization modules found.")
                logger.warning("No visualization modules found.")
            else:
                # Create tabs for each visualization
                viz_tab_names = [viz.__name__.replace('_', ' ').title() for viz in visualizations]
                viz_tabs = st.tabs(viz_tab_names)
                for tab, viz in zip(viz_tabs, visualizations):
                    with tab:
                        try:
                            viz(summary)
                            logger.info(f"Executed visualization: {viz.__module__}")
                        except Exception as e:
                            st.error(f"❌ Error in visualization {viz.__module__}: {e}")
                            logger.error(f"Visualization {viz.__module__} error: {e}")

    # Provide download links for CSV files
    st.subheader("💾 Download Simulation Results")
    simulations = get_available_simulations(output_dir='data/simulations/')
    if simulations:
        # Dropdown to select simulation
        simulation_options = [sim['simulation_id'] for sim in simulations]
        selected_simulation_id = st.selectbox("Select a Simulation to View", simulation_options)
        
        # Find the selected simulation
        selected_sim = next((sim for sim in simulations if sim['simulation_id'] == selected_simulation_id), None)
        
        if selected_sim:
            st.write(f"**Simulation Details:** {selected_sim['simulation_id']}")
            st.write(f"**Last Run:** {selected_sim['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Arrange download buttons in columns
            st.markdown("### 📥 Download Files")
            cols = st.columns(len(selected_sim['files']))
            for col, (file_type, filepath) in zip(cols, selected_sim['files'].items()):
                try:
                    df = pd.read_csv(filepath)
                    csv_buffer = convert_df_to_csv(df)
                    col.download_button(
                        label=f"Download {file_type.replace('_', ' ').title()}",
                        data=csv_buffer,
                        file_name=os.path.basename(filepath),
                        mime='text/csv'
                    )
                except FileNotFoundError:
                    col.error(f"❌ {file_type.replace('_', ' ').title()} file not found.")
                    logger.error(f"{file_type} file not found at {filepath}")
                except Exception as e:
                    col.error(f"❌ Failed to load {file_type.replace('_', ' ').title()}: {e}")
                    logger.error(f"Failed to load {filepath}: {e}")
    
            # Load and display visualizations for the selected simulation
            st.markdown("### 📈 Visualizations for Selected Simulation")
            try:
                # Load simulation summary
                summary = load_simulation_summary(selected_sim)
                
                # Load and execute all visualizations with the new summary
                visualizations = load_visualizations()
                if not visualizations:
                    st.warning("⚠️ No visualization modules found.")
                    logger.warning("No visualization modules found.")
                else:
                    # Create tabs for each visualization
                    viz_tab_names = [viz.__name__.replace('_', ' ').title() for viz in visualizations]
                    viz_tabs = st.tabs(viz_tab_names)
                    for tab, viz in zip(viz_tabs, visualizations):
                        with tab:
                            try:
                                viz(summary)
                                logger.info(f"Executed visualization: {viz.__module__}")
                            except Exception as e:
                                st.error(f"❌ Error in visualization {viz.__module__}: {e}")
                                logger.error(f"Visualization {viz.__module__} error: {e}")
            
            except Exception as e:
                st.error(f"❌ Failed to load simulation data for visualizations: {e}")
                logger.error(f"Failed to load simulation data for visualizations: {e}")

if __name__ == "__main__":
    main()
