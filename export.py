import requests
import json
import configparser
import logging
from time import sleep
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)

config = configparser.ConfigParser()
config.read("frameextractor.ini")

SECRET_TOKEN = config["FrameExtractor"]["SECRET_TOKEN"]
FRAMEEXTRACTOR_URL = config["FrameExtractor"]["BASE_URL"]


def download_snapshot(base_url, token, dl_path):
    headers = {"Authorization": token}
    response = requests.get(f"{base_url}/export", headers=headers, stream=True)

    if response.ok:
        content_disposition = response.headers.get("content-disposition")
        filename = os.path.basename(content_disposition.split("filename=")[1])
        filepath = os.path.join(dl_path, filename)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024):
                if chunk:  # filter out keep-alive new
                    f.write(chunk)

    else:
        raise ValueError(
            f"Export failed with status code {response.status_code}, response: {response.text}"
        )


if __name__ == "__main__":
    dl_path = "download"
    Path(dl_path).mkdir(exist_ok=True)
    try:
        download_snapshot(FRAMEEXTRACTOR_URL, SECRET_TOKEN, dl_path)
    except Exception as e:
        logging.error(f"download_snapshot: {e}")
