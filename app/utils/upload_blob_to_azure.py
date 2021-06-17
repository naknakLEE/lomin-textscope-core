import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__


try:
    print('\033[96m' + f"Azure Blob Storage v {__version__} - Python quickstart sample" + '\033[m')
except Exception as ex:
    print('Exception:')
    print(ex)

connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
print('\033[96m' + f"\n{connect_str}" + '\033[m')

# sl2JAk7SdA8Wf7/o1gIw5jfM0UaA+C5F16UfdDvkeC/9EE1CkhTSIRYoNdUBMy49Racupj9H/E+YnN6WKTYk0g==
# DefaultEndpointsProtocol=https;AccountName=cs1100320013a1502d2;AccountKey=sl2JAk7SdA8Wf7/o1gIw5jfM0UaA+C5F16UfdDvkeC/9EE1CkhTSIRYoNdUBMy49Racupj9H/E+YnN6WKTYk0g==;EndpointSuffix=core.windows.net

# Create the BlobServiceClient object which will be used to create a container client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Create a unique name for the container
# container_name = str(uuid.uuid4())
container_name = "textscope"
print('\033[96m' + f"\nContainer_name: {container_name}" + '\033[m')

# Create the container if not exist
container_client = blob_service_client.get_container_client(container_name)

# Create a file in the local data directory to upload and download
import json
from os import path
from app.common.const import get_settings
settings = get_settings()
def load_json(path):
    with open(path, mode='r', encoding='utf-8') as f:
        data = f.read()
    return json.loads(data)

service_cfg = load_json(settings.SERVICE_CFG_PATH)['idcard']['resources']
upload_file_paths = {}
for cfg in service_cfg:
    upload_file_paths[cfg['name']] = path.join(settings.BASE_PATH, cfg['model_path'])

# Create a blob client using the local file name as the name for the blob
print('\033[96m' + f"\nUploading to Azure Storage as blob:" + '\033[m')
for model_file_name, upload_file_path in upload_file_paths.items():
    print('\033[96m' + f"\n\t{model_file_name}" + '\033[m')
    blob_client = blob_service_client.get_blob_client(
        container=container_name, 
        blob=model_file_name
    )

    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data)

print('\033[35m' + "\nListing blobs..." + '\033[m')
# List the blobs in the container
blob_list = container_client.list_blobs()
for blob in blob_list:
    print('\033[96m' + f"\t{blob.name}" + '\033[m')
