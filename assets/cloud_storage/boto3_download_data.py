import os
import argparse

try:
    import boto3
    import botocore
    from hydra import initialize_config_dir, compose
    from dotenv import load_dotenv, find_dotenv
    from alive_progress import alive_bar
except:
    os.system("pip3 install boto3 botocore hydra-core python-dotenv alive_progress")
    import boto3
    import botocore
    from dotenv import load_dotenv, find_dotenv
    from alive_progress import alive_bar

from typing import List
from pathlib import Path, PurePath


load_dotenv(find_dotenv())
base_dir = Path(__file__).resolve().parent.parent.parent

def bold_print(contents: str) -> None:
    print("\033[1m" + contents + "\033[0m")


def get_boto3_session() -> boto3.Session:
    return boto3.Session(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("REGION_NAME"),
    )


def get_download_list(
    bucket,  download_object_name: str, pre_fix: str) -> List:
    download_list = list()
    for obj in bucket.objects.filter(Prefix = pre_fix):
        if download_object_name in obj.key.split("/"):
            object_name = PurePath(
                base_dir, obj.key.split(pre_fix)[-1]
            ).as_posix()
            if not os.path.exists(os.path.dirname(object_name)):
                os.makedirs(os.path.dirname(object_name))
            download_list.append((obj.key, object_name))  # (object key, object name)
    return download_list


def download_dir_from_s3(
    bucket_name: str,
    download_object_name: str,
    pre_fix: str,
) -> None:
    s3_resource = get_boto3_session().resource("s3")
    bucket = s3_resource.Bucket(bucket_name)
    download_list = get_download_list(bucket, download_object_name, pre_fix)
    with alive_bar(len(download_list), title="Download s3 data", bar="smooth") as bar:
        for object_key, object_name in download_list:
            try:
                bold_print("Download {} to {}".format(object_key, object_name))
                if Path(object_name).exists():
                    bold_print("{} already exist.".format(object_name))
                else:
                    bucket.download_file(object_key, object_name)
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    bold_print("The object does not exist.")
                else:
                    raise
            bar()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bucket_name", required=False, type=str, default="lomin-model-repository"
    )
    parser.add_argument("--pre_fix", required=False, type=str, default="textscope/")
    parser.add_argument("--download_object_name", required=True, type=str)
    args = parser.parse_args()

    
    download_dir_from_s3(
        args.bucket_name, args.download_object_name, args.pre_fix
    )
