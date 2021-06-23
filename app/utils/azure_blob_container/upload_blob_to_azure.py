import os
import json
import sys

from azure.storage.blob import BlobServiceClient, __version__
from os import path

sys.append("/workspace")
from app.common.const import get_settings


settings = get_settings()
connect_str = settings.AZURE_STORAGE_CONNECTION_STRING
container_name = "textscope"


try:
    print(
        "\033[96m"
        + f"Azure Blob Storage v {__version__} - Python quickstart sample"
        + "\033[m"
    )
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


service_cfg = load_json(settings.SERVICE_CFG_PATH)["idcard"]["resources"]
service_env = settings.SERVICE_ENV_PATH
upload_file_paths = {}
for cfg in service_cfg:
    upload_file_paths[cfg["name"]] = path.join(settings.BASE_PATH, cfg["model_path"])
upload_file_paths[".env"] = service_env

# Create a blob client using the local file name as the name for the blob
print("\033[96m" + f"\nUploading to Azure Storage as blob:" + "\033[m")
for model_file_name, upload_file_path in upload_file_paths.items():
    print("\033[95m" + f"\t{model_file_name}" + "\033[m")
    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=upload_file_path.split("/")[-1]
    )

    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data)

# List the blobs in the container
print("\033[35m" + "\nListing blobs..." + "\033[m")
blob_list = container_client.list_blobs()
for blob in blob_list:
    print("\033[95m" + f"\t{blob.name}" + "\033[m")
