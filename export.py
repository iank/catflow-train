import requests
import json
import configparser
import logging
import sys
import os
import time
from pathlib import Path
from label_studio import LabelStudioAPI
from urllib.parse import urlparse


# Setup logging
logging.basicConfig(level=logging.INFO)

config = configparser.ConfigParser()
config.read("frameextractor.ini")

api = LabelStudioAPI(
    config["LabelStudioAPI"]["BASE_URL"], config["LabelStudioAPI"]["AUTH_TOKEN"]
)

# Create a snapshot on the server
logging.info("Creating snapshot")
export_id, snapshot_name = api.create_snapshot(config["LabelStudioAPI"]["PROJECT_ID"])
if export_id is None:
    logging.error("/export: Failed to create snapshot")
    sys.exit(1)

# Check the status until the snapshot is created
completed = False
while not completed:
    logging.info("Checking if snapshot is ready...")
    completed = api.check_export_status(config["LabelStudioAPI"]["PROJECT_ID"], export_id)
    time.sleep(1)

# Download the archive
logging.info("Downloading snapshot")
response = api.download_snapshot(config["LabelStudioAPI"]["PROJECT_ID"], export_id, "JSON")
uuid_src_pairs = {}
if response.ok:
    data = json.loads(response.content.decode('utf-8'))
    img_src = [(x['data']['image'],x['data']['meta']) for x in data if 'meta' in x['data']]
    for img in img_src:
        uuid = os.path.basename(urlparse(img[0]).path).split(".")[0]
        if isinstance(img[1], dict):
            src = img[1]['source']
        else:
            src = json.loads(img[1])['source']

        uuid_src_pairs[uuid] = src

# Convert the created snapshot to YOLO
logging.info("Converting snapshot to YOLO format")
api.convert_snapshot(config["LabelStudioAPI"]["PROJECT_ID"], export_id, "YOLO")

# Check the status until the conversion is complete
completed = False
while not completed:
    logging.info("Checking if conversion is complete...")
    completed = api.check_conversion_status(
        config["LabelStudioAPI"]["PROJECT_ID"], export_id, "YOLO"
    )
    time.sleep(1)

# Download the archive
logging.info("Downloading snapshot")
response = api.download_snapshot(config["LabelStudioAPI"]["PROJECT_ID"], export_id)
if response.ok:
    dl_path = "download"
    Path(dl_path).mkdir(exist_ok=True)

    content_disposition = response.headers.get("content-disposition")
    filename = f"{snapshot_name}.zip"
    filepath = os.path.join(dl_path, filename)

    logging.info(f"Writing snapshot to {filepath}")
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(1024):
            if chunk:  # filter out keep-alive new
                f.write(chunk)

    filename = f"{snapshot_name}.json"
    filepath = os.path.join(dl_path, filename)

    logging.info(f"Writing snapshot sources to {filepath}")
    with open(filepath, "w") as f:
        f.write(json.dumps(uuid_src_pairs))
