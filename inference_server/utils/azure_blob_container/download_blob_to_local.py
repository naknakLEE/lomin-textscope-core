import os
import json

from azure.storage.blob import BlobServiceClient, __version__
from os import path

from inference_server.common.const import get_settings


settings = get_settings()
connect_str = settings.AZURE_STORAGE_CONNECTION_STRING
container_name = "textscope"


try:
    print("\033[96m" + f"Azure Blob Storage v {__version__} - Python quickstart sample" + "\033[m")
except Exception as ex:
    print("Exception:")
    print(ex)

# Create the BlobServiceClient object which will be used to create a container client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Create the container if not exist
print("\033[96m" + f"Container_name: {container_name}" + "\033[m")
container_client = blob_service_client.get_container_client(container_name)

# Create a file in the local data directory to upload and download
def load_json(path):
    with open(path, mode="r", encoding="utf-8") as f:
        data = f.read()
    return json.loads(data)


service_cfg = load_json(settings.SERVICE_CFG_PATH)["document"]["resources"]
service_env = settings.SERVICE_ENV_PATH
download_file_paths = {}
for cfg in service_cfg:
    download_file_paths[cfg["model_path"].split("/")[-1]] = path.join(
        settings.BASE_PATH, cfg["model_path"]
    )
download_file_paths[".env"] = service_env

# Download blobs (model, env)
blob_list = container_client.list_blobs()
print("\033[35m" + "\nListing blobs..." + "\033[m")
for blob in blob_list:
    if blob.name not in download_file_paths:
        continue
    print("\033[95m" + f"\t{blob.name}" + "\033[m")
    model_file_path = download_file_paths[blob.name]
    # if you want't overwrite from download file to exist file
    # if blob.name == ".env":
    #     model_file_path = model_file_path.replace(".env", "_DOWNLOADED.env")
    # else:
    #     model_file_path = model_file_path.replace(".onnx", "_DOWNLOADED.onnx")

    bytes = container_client.get_blob_client(blob).download_blob().readall()
    os.makedirs(os.path.dirname(model_file_path), exist_ok=True)
    with open(model_file_path, "wb") as file:
        file.write(bytes)
