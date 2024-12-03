import os
import importlib
import logging

logger = logging.getLogger(__name__)

def load_visualizations():
    """
    Dynamically imports all visualization modules in the dataviz directory and returns their display functions.

    Returns:
        list: List of display functions from each visualization module.
    """
    visualizations = []
    dataviz_dir = os.path.dirname(__file__)

    for filename in os.listdir(dataviz_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            full_module_name = f'app.dataviz.{module_name}'
            try:
                module = importlib.import_module(full_module_name)
                if hasattr(module, 'display'):
                    visualizations.append(module.display)
                    logger.info(f"Loaded visualization module: {full_module_name}")
                else:
                    logger.warning(f"Module {full_module_name} does not have a 'display' function.")
            except Exception as e:
                logger.error(f"Failed to import module {full_module_name}: {e}")

    return visualizations
