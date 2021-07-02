from cryptography.fernet import Fernet
import io
import json
import yaml
from PIL import Image


def read_file(path, key):
    fernet = Fernet(key)
    with open(path, "rb") as f:
        data = f.read()
    data = fernet.decrypt(data)
    return data


def png_solver(path, key):
    data = read_file(path, key)
    data = io.BytesIO(data)
    return Image.open(data)


def txt_solver(path, key):
    data = read_file(path, key)
    return data.decode("utf-8")


def json_solver(path, key):
    data = read_file(path, key)
    return json.loads(data.decode("utf-8"))


def yaml_solver(path, key):
    data = read_file(path, key)
    return yaml.safe_load(data.decode("utf-8"))


def onnx_solver(path, key):
    data = read_file(path, key)
    return io.BytesIO(data)


def pth_solver(path, key):
    data = read_file(path, key)
    return io.BytesIO(data)
