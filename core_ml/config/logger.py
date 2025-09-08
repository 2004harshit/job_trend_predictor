import logging
import logging.config
import yaml
import os

def setup_logging(config_path="config/config.yaml"):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    logging_config = config.get("logging", {})
    if logging_config:
        # Ensure logs directory exists
        log_file = logging_config["handlers"]["file"]["filename"]
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        logging.config.dictConfig(logging_config)
    else:
        logging.basicConfig(level=logging.INFO)  # fallback
