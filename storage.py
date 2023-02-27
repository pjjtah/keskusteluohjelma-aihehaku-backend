import os
import time
import boto3
from dotenv import load_dotenv

load_dotenv()

ACCESS_ID = os.environ.get('STORAGE_ACCESS_ID')
SECRET_KEY = os.environ.get('STORAGE_SECRET_KEY')

# Initiate session
session = boto3.session.Session()
client = session.client('s3',
                        region_name='ams3',
                        endpoint_url='https://ams3.digitaloceanspaces.com',
                        aws_access_key_id=ACCESS_ID,
                        aws_secret_access_key=SECRET_KEY)


def upload_data():
    try:
        client.upload_file('data.json', 'keskustelustorage', 'data.json')
    except Exception as ex:
        print('Exception:')
        print(ex)


def download_data():
    try:
        client.download_file('keskustelustorage',
                             'data.json',
                             'data.json')
    except Exception as ex:
        print('Exception:')
        print(ex)


def upload_tags():
    try:
        client.upload_file('tags.json', 'keskustelustorage', 'tags.json')
    except Exception as ex:
        print('Exception:')
        print(ex)


def upload_tags_backup():
    try:
        client.upload_file('tags.json', 'keskustelustorage', 'tags-' + time.strftime("%Y%m%d-%H%M%S") + '.json' )
    except Exception as ex:
        print('Exception:')
        print(ex)


def upload_watches():
    try:
        client.upload_file('watches.json', 'keskustelustorage', 'watches.json')
    except Exception as ex:
        print('Exception:')
        print(ex)


def upload_suggestions():
    try:
        client.upload_file('suggestions.json', 'keskustelustorage', 'suggestions.json')
    except Exception as ex:
        print('Exception:')
        print(ex)


def download_tags():
    try:
        client.download_file('keskustelustorage',
                             'tags.json',
                             'tags.json')
    except Exception as ex:
        print('Exception:')
        print(ex)


def download_watches():
    try:
        client.download_file('keskustelustorage',
                             'watches.json',
                             'watches.json')
    except Exception as ex:
        print('Exception:')
        print(ex)


def download_suggestions():
    try:
        client.download_file('keskustelustorage',
                             'suggestions.json',
                             'suggestions.json')
    except Exception as ex:
        print('Exception:')
        print(ex)


def upload_users():
    try:
        client.download_file('keskustelustorage',
                             'users.json',
                             'users.json')
    except Exception as ex:
        print('Exception:')
        print(ex)

