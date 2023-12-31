import numpy as np
import glob
import os
import configparser
import shutil
import random
import requests
import json
import logging
import requests
import json
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_filenames(folder):
    filenames = set()

    for path in glob.glob(os.path.join(folder, '*.txt')):
        filename = os.path.split(path)[-1]
        filenames.add(filename)

    return filenames

def download_images(endpoint_url, image_filenames):
    session = requests.Session()

    total_images = len(image_filenames)
    digit_len = len(str(total_images))    # For pretty status updates

    logger.info("Downloading missing images:")
    for idx,image_filename in enumerate(image_filenames):
        url = f'{endpoint_url}/{image_filename}'
        destination = f'download/images/{image_filename}'
        if not os.path.isfile(destination):
            try:
                response = session.get(url, timeout=5)
                if response.ok:
                    with open(destination, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"[{idx:{digit_len}d}/{total_images}] {image_filename}")
                else:
                    logger.error(f"Failed to download {url}. HTTP status code: {response.status_code}")
            except requests.exceptions.RequestException as err:
                logger.error(f"Error occurred: {err}")
                raise SystemExit("Timeout occurred. Exiting the program.")
        else:
            logger.info(f"[{idx:{digit_len}d}/{total_images}] {image_filename} (Cached)")

random.seed(42)

def shuffle_and_split(sources, train_ratio=0.7):
    # Separate sources into empty and non-empty
    empty_sources = [source for source in sources if source is None ]
    non_empty_sources = [source for source in sources if source is not None]

    # Shuffle and split only the non-empty sources
    random.shuffle(non_empty_sources)
    split_index = int(train_ratio * len(non_empty_sources))

    # Append empty sources to the training set
    train_sources = non_empty_sources[:split_index] + empty_sources
    val_sources = non_empty_sources[split_index:]

    return train_sources, val_sources

def copy_files(filenames, src_folder, dst_folder):
    for filename in filenames:
        file_extension = '.png' if 'images' in src_folder else '.txt'
        src_file = os.path.join(src_folder, filename + file_extension)
        dest_file = os.path.join(dst_folder, filename + file_extension)
        shutil.copyfile(src_file, dest_file)

config = configparser.ConfigParser()
config.read('frameextractor.ini')

ENDPOINT_URL = config['S3']['ENDPOINT_URL']

if len(sys.argv) != 2:
    print('Usage: python split_data.py downloads/<json-file>')
    sys.exit(1)

json_file = sys.argv[1]

with open(json_file, 'r') as file:
    uuid_source_pairs = json.load(file)

label_filenames = get_filenames('download/labels')
label_filenames = np.array(list(label_filenames))

# Check and download missing images
image_filenames = [filename.replace('.txt', '.png') for filename in label_filenames]
download_images(ENDPOINT_URL, image_filenames)

# Fetch source per uuid
uuids = set([filename.replace('.txt', '') for filename in label_filenames])

# Group filenames by source
uuid_source_pairs = {uuid: source for uuid, source in uuid_source_pairs.items() if uuid in uuids}

source_to_filenames = {}
for uuid, source in uuid_source_pairs.items():
    if source not in source_to_filenames:
        source_to_filenames[source] = []
    source_to_filenames[source].append(uuid)

# Split sources
sources = list(source_to_filenames.keys())
train_sources, val_sources = shuffle_and_split(sources)

if not os.path.exists('data'):
    for folder in ['images', 'labels']:
        for split in ['train', 'val']:
            os.makedirs(f'data/{folder}/{split}')

# Copy files to train/val folders
for source in train_sources:
    copy_files(source_to_filenames[source], 'download/labels', 'data/labels/train')
    copy_files(source_to_filenames[source], 'download/images', 'data/images/train')

for source in val_sources:
    copy_files(source_to_filenames[source], 'download/labels', 'data/labels/val')
    copy_files(source_to_filenames[source], 'download/images', 'data/images/val')
