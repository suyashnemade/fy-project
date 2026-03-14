"""
Entry point for running the desktop_app package directly (e.g. `python -m desktop_app`).
"""
from core.logger import get_logger
from .app import main

if __name__ == "__main__":
    # Initialize the centralized logger for the application start
    logger = get_logger("semantic_image_search")
    logger.info("Starting Semantic Image Search application (module entry)...")
    main()
