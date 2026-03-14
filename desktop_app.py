"""
Backward-compatible entry point for the desktop application.
Please use `python -m desktop_app` instead.
"""
from core.logger import get_logger
from desktop_app.app import main

if __name__ == "__main__":
    # Initialize the centralized logger for the application start
    logger = get_logger("semantic_image_search")
    logger.info("Starting Semantic Image Search application (backward-compat entry)...")
    main()
