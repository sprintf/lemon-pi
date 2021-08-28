import os
import requests
import tarfile
import tempfile
from datetime import datetime, timedelta

from google.cloud import storage


def upload_blob(source_file_name, destination_blob_name):
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

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", dir="/tmp") as tmpfile:
        with tarfile.open(fileobj=tmpfile, mode="w:gz") as tar:
            if os.path.exists("/var/lib/lemon-pi"):
                tar.add("/var/lib/lemon-pi/track-data", recursive=True)
            for f in os.listdir("logs"):
                filedate = datetime.fromtimestamp(os.path.getmtime('logs/' + f)).date()
                if filedate > recent:
                    if f.startswith("gps") or f == "lemon-pi.log":
                        tar.add("logs/" + f)

        upload_blob(tmpfile.name, os.path.split(tmpfile.name)[1])


def get_mac_address():
    with open('/sys/class/net/eth0/address') as f:
        return f.readline().strip()


def get_credentials():
    """ fetch the credentials to upload diagnostic data, only registered mac addresses
        are valid """
    r = requests.post('https://us-west2-perplexus-gps.cloudfunctions.net/credential-agent',
                      json={"mac": get_mac_address()}, )
    if r.status_code != 200:
        raise Exception(f"failed to retrieve credentials, got code {r.status_code} {r.text}")
    return r.text


if __name__ == "__main__":
    creds = get_credentials()

    # unfortunately the credentials file has to be passed as a named file, so
    # the credentials are written to a temporary file, and then the upload occurs
    with tempfile.NamedTemporaryFile(suffix=".json", dir="/tmp") as cred_file:
        cred_file.write(creds.encode("UTF-8"))
        cred_file.flush()
        cred_file.seek(0)

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_file.name
        create_tar_and_upload()