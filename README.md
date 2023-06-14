# catflow-train

Export and model training for an object recognition data pipeline

# Set up:

In your virtualenv,

```
pip install -r requirements.txt
git clone https://github.com/ultralytics/yolov5

# This torch version is necessary on my GPU for numerical stability. YMMV
pip install torch==1.7.1+cu101 torchvision==0.8.2+cu101 torchaudio==0.7.2 \
    -f https://download.pytorch.org/whl/torch_stable.html

pip install -r yolov5/requirements.txt
```

# Configure model

Write a `your_model.yaml` file according to your dataset, for example:

```
# Dataset paths relative to the yolov5 folder
path: ../data
train: images/train
val:   images/val

# Number of classes
nc: 3

# Class names corresponding to your labels (class 0, 1, ...)
names: ['cat', 'dog', 'human']
```

# Get data

First, write frameextractor.ini, for example:

```
[FrameExtractor]
SECRET_TOKEN = XXXXXXXX
BASE_URL = https://frameextractor.example.com/
```

This should point to
[catflow-frameextractor](https://github.com/iank/catflow-frameextractor).

Then run export.py:

```
python export.py
```

Extract the zip in `download/` and check download/notes.json against your yaml file.

Download missing images and split the dataset (delete the `data/` directory first if this is a re-run):

```
python split_data.py
```

# Train:

```
pip install comet_ml # optional
export COMET_API_KEY=<COMET_API_KEY>   # optional
python yolov5/train.py --data your_model.yaml --weights yolov5m.pt \
    --epochs 30 --batch 16 --freeze 10
```
