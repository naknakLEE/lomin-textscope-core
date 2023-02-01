from typing import List, Any, Optional, Dict
from os import path
from tests.bsn_2207_lina.utils.const import Const
import requests

constants = Const()
_root_url=constants.INTEGRATED_API_ROOT_URL

def get_dotenv(env_file: str):
    env_vars = [] # or dict {}
    with open(env_file) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            # if 'export' not in line:
            #     continue
            # Remove leading `export `, if you have those
            # then, split name / value pair
            # key, value = line.replace('export ', '', 1).strip().split('=', 1)
            key, value = line.strip().split('=', 1)
            # os.environ[key] = value  # Load to local environ
            # env_vars[key] = value # Save to a dict, initialized env_vars = {}
            env_vars.append({'name': key, 'value': value}) # Save to a list

    print(env_vars)
    return env_vars

# reqeust post upload file
def post_upload_file(file_path: str, token: str):
    url_path = "/api/v1/docx"
    url = _root_url + url_path
    
    document_id = None
    with open(file_path, "rb") as f:
        response = requests.post(url,headers={"accept": f"application/json", "Authorization": f"Bearer {token}"},files={"file": f},)
        
        if response.status_code == 200:
            document_id = response.json().get("document_id")
        else:
            print(f"request error: {response.status_code} {response.json()}")

    return document_id

def convert_list_value_to_none(inf_response: List[Any]) -> Optional[List[Any]]:
    if len(inf_response) == 0:
        return None

    first_of_list = inf_response[0]
    
    if isinstance(first_of_list, dict):
        none_dict = convert_dict_value_to_none(first_of_list)
    else:
        return None
    return [none_dict]
    

def convert_dict_value_to_none(inf_response: Dict[str, Any]) -> Dict[str, Any]:
    include_keys = ['key_value', 'key_values', 'texts', 'tables', 'span', 'key_code']
    for key, value in inf_response.items():
        if isinstance(value, dict):
            inf_response[key] = convert_dict_value_to_none(value)
        elif isinstance(value, list) and key in include_keys:
            inf_response[key] = convert_list_value_to_none(value)
        else:
            inf_response[key] = None
    return inf_response

def get_project_root_dir():
    return path.join(path.dirname(path.realpath(__file__)), "../../../")