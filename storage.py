import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from datetime import date

connect_str = os.environ['connect_str']
container_name = os.environ['container_name']
container_client = ContainerClient.from_connection_string(connect_str, container_name)


def upload_data():
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        blob = BlobClient.from_connection_string(conn_str=connect_str, container_name=container_name, blob_name="data.json")
        backup_name = "data-" + date.today().strftime("%d-%m-%Y") + ".json"
        # create backup from old tags, delete it and upload it again with timestamp
        if blob.exists():
            with open(backup_name, "wb") as my_blob:
                blob_data = blob.download_blob()
                blob_data.readinto(my_blob)
            blob.delete_blob()
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=backup_name)
            with open(backup_name, "rb") as backup_tags:
                blob_client.upload_blob(backup_tags, overwrite=True)
        # upload new tags
        blob_client = blob_service_client.get_blob_client(container=container_name, blob="data.json")
        with open("data.json", "rb") as tags:
            blob_client.upload_blob(tags)
    except Exception as ex:
        print('Exception:')
        print(ex)


def upload_tags():
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        blob = BlobClient.from_connection_string(conn_str=connect_str, container_name=container_name, blob_name="tags.json")
        backup_name = "tags-" + date.today().strftime("%d-%m-%Y") + ".json"
        # create backup from old tags, delete it and upload it again with timestamp
        if blob.exists():
            with open(backup_name, "wb") as my_blob:
                blob_data = blob.download_blob()
                blob_data.readinto(my_blob)
            blob.delete_blob()
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=backup_name)
            with open(backup_name, "rb") as backup_tags:
                blob_client.upload_blob(backup_tags, overwrite=True)
            print("backup of tags stored into azure")
        # upload new tags
        blob_client = blob_service_client.get_blob_client(container=container_name, blob="tags.json")
        with open("tags.json", "rb") as tags:
            blob_client.upload_blob(tags)
    except Exception as ex:
        print('Exception:')
        print(ex)


def download_tags():
    try:
        blob = BlobClient.from_connection_string(conn_str=connect_str, container_name=container_name, blob_name="tags.json")
        if blob.exists():
            with open("tags.json", "wb") as tags:
                blob_data = blob.download_blob()
                blob_data.readinto(tags)
                print("tags loaded from azure")
    except Exception as ex:
        print('Exception:')
        print(ex)