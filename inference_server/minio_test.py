from minio import Minio
from minio.error import S3Error


def main():
    # Create a client with the MinIO server playground, its access key
    # and secret key.
    client = Minio(
        "0.0.0.0",
        access_key="minioadmin",
        secret_key="minioadmin",
    )

    # Make 'asiatrip' bucket if not exist.
    found = client.bucket_exists("asiatrip")
    if not found:
        client.make_bucket("asiatrip")
    else:
        print("Bucket 'asiatrip' already exists")

    # Upload '/home/shinuk/Downloads/test.jpg' as object name
    # 'asiaphotos-2015.zip' to bucket 'asiatrip'.
    client.fput_object(
        "asiatrip",
        "asiaphotos-2015.zip",
        "/home/shinuk/Downloads/test.jpg",
    )
    print(
        "'/home/shinuk/Downloads/test.jpg' is successfully uploaded as "
        "object 'asiaphotos-2015.zip' to bucket 'asiatrip'."
    )


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
