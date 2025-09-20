import logging

# Configure basic logging (e.g., to console with INFO level and a simple format)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance
logger = logging.getLogger(__name__)