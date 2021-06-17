import os
import json

from azure.storage.blob import BlobServiceClient, __version__
from os import path

from app.common.const import get_settings


settings = get_settings()
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')


try:
    print('\033[96m' + f"Azure Blob Storage v {__version__} - Python quickstart sample" + '\033[m')
except Exception as ex:
    print('Exception:')
    print(ex)

# Create the BlobServiceClient object which will be used to create a container client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Create a unique name for the container
# container_name = str(uuid.uuid4())
container_name = "textscope"
print('\033[96m' + f"\nContainer_name: {container_name}" + '\033[m')

# Create the container if not exist
container_client = blob_service_client.get_container_client(container_name)

# Create a file in the local data directory to upload and download
def load_json(path):
    with open(path, mode='r', encoding='utf-8') as f:
        data = f.read()
    return json.loads(data)

service_cfg = load_json(settings.SERVICE_CFG_PATH)['idcard']['resources']
service_env = settings.SERVICE_ENV_PATH
download_file_paths = {}
for cfg in service_cfg:
    download_file_paths[cfg['name']] = path.join(settings.BASE_PATH, cfg['model_path'])
download_file_paths['.env'] = service_env

blob_list = container_client.list_blobs()
# List the blobs in the container

print('\033[35m' + f"{download_file_paths}" + '\033[m')

print('\033[35m' + "\nListing blobs..." + '\033[m')
for blob in blob_list:
    print('\033[95m' + f"\t{blob.name}" + '\033[m')
    model_file_path = download_file_paths[blob.name]
    if blob.name == '.env':
        download_file_path = model_file_path.replace('.env', '_DOWNLOADED.env')
    else: 
        download_file_path = model_file_path.replace('.onnx', '_DOWNLOADED.onnx')
        
    bytes = container_client.get_blob_client(blob).download_blob().readall()
    with open(download_file_path, "wb") as file:
        file.write(bytes)

# # Download the blob(s).
# # Add '_DOWNLOADED' as prefix to '.onnx' so you can see both files.
# for model_file_name, upload_file_path in download_file_paths.items():
#     full_path_to_file2 = os.path.join(upload_file_path, model_file_name.replace(
#    '.onnx', '_DOWNLOADED.onnx'))
#     print('\033[95m' + f"\nDownloading blob to {full_path_to_file2}"  + '\033[m')
#     container_client.download_blob(
#         container_name, model_file_name, full_path_to_file2)