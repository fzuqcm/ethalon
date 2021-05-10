# Etalon Software

## Install

> This is the recommended setup tested on good operations system

Open two VSCode windows for `driver` and `web` folders. Then only operate within the folders. **You should not run any command directly in the project root folder.**

### Driver

```sh
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Web

```sh
npm install
```

## Development

### Driver

```sh
# inside virtual environment
python app.py
```

### Web

```sh
npm run dev
```

### Production

There no scripts for production bundle. Web can be easily bundled as a serie of `.js`/`.css` files and staticly served. The great question is how to deal with Python installation.

One solution could be to use [Snap](https://snapcraft.io/). It's a multi-platform installer.