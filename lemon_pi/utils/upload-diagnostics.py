import os
import tarfile
import tempfile
from datetime import datetime, timedelta

from google.cloud import storage


def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client(client_info=None)
    bucket = storage_client.bucket("normtronix-upload")
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )


def create_tar_and_upload():
    recent = datetime.now().date() - timedelta(days=2)

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", dir="/tmp", delete=False) as tmpfile:
        with tarfile.open(fileobj=tmpfile, mode="w:gz") as tar:
            if os.path.exists("/var/lib/lemon-pi"):
                tar.add("/var/lib/lemon-pi/track-data", recursive=True)
            for f in os.listdir("logs"):
                filedate = datetime.fromtimestamp(os.path.getmtime('logs/' + f)).date()
                if filedate > recent:
                    if f.startswith("gps") or f == "lemon-pi.log":
                        tar.add("logs/" + f)

    upload_blob(tmpfile.name, os.path.split(tmpfile.name)[1])


if __name__ == "__main__":
    create_tar_and_upload()