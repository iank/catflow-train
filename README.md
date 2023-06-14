# catflow-train

Export and model training for an object recognition data pipeline

# Set up:

In your virtualenv,

```
pip install -r requirements.txt
```

# Get data

First, write frameextractor.ini, for example:

```
[FrameExtractor]
SECRET_TOKEN = XXXXXXXX
BASE_URL = https://frameextractor.example.com/
```

This should point to
(catflow-frameextractor)[https://github.com/iank/catflow-frameextractor].

Then run export.py:

```
python export.py
```
