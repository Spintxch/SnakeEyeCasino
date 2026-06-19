Snake Eye Casino - Native GUI

This folder contains a PySimpleGUI frontend (`frontend/snake_eye_gui.py`) and backend logic (`backend/casinoBackEnd.py`).

Version

- `snake_eye_casino.__version__` = `0.1.0`

Quick start

1. Create a virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the native GUI directly from the package root:

```bash
python -m snake_eye_casino
```

Alternative direct launch from the package folder:

```bash
python frontend\snake_eye_gui.py
```

Build .exe (Windows) using PyInstaller

1. Install PyInstaller:

```bash
pip install pyinstaller
```

2. Build the .exe (one-file) from the package root:

```bash
pyinstaller --onefile --noconsole frontend\snake_eye_gui.py
```

The generated executable will be in the `dist` folder.

If you want to share the final app, use the `release` folder:

- `release\snake_eye_gui.exe`

Just zip the `release` folder and send that to a friend.
