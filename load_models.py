import logging
import os
from faster_whisper import WhisperModel, download_model

# Setup logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("download_model.log"),
            logging.StreamHandler()
        ]
    )

def main():
    model_dir = "./models"
    model_name = os.environ.get('MODEL_NAME', "small")
    path = f"./{model_dir}/{model_name}"

    # Ensure logging is set up
    setup_logging()

    logging.info(f"Model directory is set to: {model_dir}")
    logging.info(f"Model name is set to: {model_name}")

    # Create the model directory if it doesn't exist
    if not os.path.exists(model_dir):
        logging.info(f"Creating model directory: {model_dir}")
        os.makedirs(model_dir)

    # Download the model if it doesn't already exist
    if not os.path.exists(path):
        try:
            logging.info(f"Downloading model: {model_name} to {path}")
            download_model(model_name, output_dir=path)
            logging.info(f"Successfully downloaded model: {model_name} to {path}")
        except Exception as e:
            logging.error(f"Failed to download model: {model_name}. Error: {str(e)}")
    else:
        logging.info(f"Model {model_name} already exists at {path}")

if __name__ == "__main__":
    main()
