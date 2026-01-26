import logging
import logging.config
import yaml
import os

def setup_logging(config_path=None):
    """
    Setup logging from a YAML config file.
    Ensures the log directory exists before configuring handlers.
    """ 
    # Default path to logging.yml in the same folder as this file
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config\logging.yml")
   

    print("Loading logging config from:", config_path)

    # Load YAML
    print(config_path)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Ensure directories for file handlers exist
    for handler in config.get("handlers", {}).values():
        if "filename" in handler:
            # Make path absolute relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            handler["filename"] = os.path.join(project_root, handler["filename"])
            os.makedirs(os.path.dirname(handler["filename"]), exist_ok=True)

            print("-"*50)
            print("Handler : ", handler)
            print("Log file : ", handler["filename"])
            print("file root ", project_root)
            print("-"*50)
            print()

    # Configure logging
    logging.config.dictConfig(config)
    logging.info("Logging is configured successfully.")

if __name__ == "__main__":
    setup_logging()