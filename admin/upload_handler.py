# admin/upload_handler.py

import os
import logging

logger = logging.getLogger(__name__)

def upload_projection_file(uploaded_file, upload_dir: str = 'data/projections/user_uploads/') -> str:
    """
    Saves the uploaded projection file to the user_uploads directory.

    Args:
        uploaded_file: The uploaded file object from Streamlit.
        upload_dir (str): Directory where uploaded projections are stored.

    Returns:
        str: Path to the saved projection file.
    """
    try:
        os.makedirs(upload_dir, exist_ok=True)
        filename = os.path.basename(uploaded_file.name)
        destination = os.path.join(upload_dir, filename)
        with open(destination, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logger.info(f"Projection file uploaded and saved to {destination}")
        return destination
    except Exception as e:
        logger.error(f"Failed to upload projection file: {e}")
        raise
