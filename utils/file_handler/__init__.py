import os
import importlib
import logging

logger = logging.getLogger(__name__)

def load_file_handlers():
    """
    Dynamically imports all file handler modules in the file_handler directory and returns their handle functions.

    Returns:
        dict: Dictionary mapping module names to their handle functions.
    """
    file_handlers = {}
    fh_dir = os.path.dirname(__file__)

    for filename in os.listdir(fh_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            full_module_name = f'utils.file_handler.{module_name}'
            try:
                module = importlib.import_module(full_module_name)
                if hasattr(module, 'handle'):
                    file_handlers[module_name] = module.handle
                    logger.info(f"Loaded file handler module: {full_module_name}")
                else:
                    logger.warning(f"Module {full_module_name} does not have a 'handle' function.")
            except Exception as e:
                logger.error(f"Failed to import module {full_module_name}: {e}")

    return file_handlers
