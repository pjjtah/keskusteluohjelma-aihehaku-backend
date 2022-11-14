import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from fastapi import FastAPI, status, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from schemas import UserOut, UserAuth, TokenSchema
from deps import get_current_user
import json
from os import path
from utils import (
    create_access_token,
    create_refresh_token,
    verify_password
)
# from dotenv import load_dotenv
from videoRequester import get_videos
from datetime import date

# load_dotenv()

app = FastAPI()
origins = ["*"]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connect_str = os.environ['connect_str']
container_name = os.environ['container_name']
container_client = ContainerClient.from_connection_string(connect_str, container_name)


def obj_dict(obj):
    return obj.__dict__


# get_videos()


def check_tags():
    if path.isfile("tags.json") is False:
        blob = BlobClient.from_connection_string(conn_str=connect_str, container_name=container_name,
                                                 blob_name="tags.json")
        if blob.exists():
            with open("tags.json", "wb") as my_blob:
                blob_data = blob.download_blob()
                blob_data.readinto(my_blob)
        else:
            with open("tags.json", 'w') as f:
                json.dump({"piilotettu": [""]}, f)


def check_suggestions():
    if path.isfile("suggestions.json") is False:
        blob = BlobClient.from_connection_string(conn_str=connect_str, container_name=container_name,
                                                 blob_name="suggestions.json")
        if blob.exists():
            with open("suggestions.json", "wb") as my_blob:
                blob_data = blob.download_blob()
                blob_data.readinto(my_blob)
        else:
            with open("suggestions.json", 'w') as f:
                json.dump({"testi": date.today().strftime("%d-%m-%Y")}, f)


@app.post('/kirjaudu', summary="Kirjaudu sisään", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if path.isfile("users.json") is False:
        with open("users.json", 'w') as f:
            json.dump({"id": "087cb8b7-add0-45d3-9407-d0d99d26c253", "username": os.environ.get("_username"),
                       "password": os.environ.get("_password"),
                       "access_token": "", "refresh_token": ""}, f)
    u = json.load(open('users.json', encoding='utf-8'))
    user = None

    if u["username"] == form_data.username:
        user = u

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kirjautuminen epäonnistui"
        )

    hashed_pass = user['password']
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kirjautuminen epäonnistui"
        )
    access_token = create_access_token(user['username'])
    refresh_token = create_refresh_token(user['username'])
    u["access_token"] = access_token
    u["refresh_token"] = refresh_token
    json_string = json.dumps(u, ensure_ascii=False)
    json_file = open("users.json", "w", encoding="utf-8")
    json_file.write(json_string)
    json_file.close()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@app.post('/tagit', summary='Luo uusi tagi')
async def create_tag(nimi: str, response: Response, user=Depends(get_current_user)):
    nimi = nimi.lower()
    check_tags()
    with open("tags.json") as f:
        tags = json.load(f)
    if nimi in tags:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return "Tagi " + nimi + " on jo olemassa"
    tags[nimi] = [nimi]
    with open("tags.json", 'w') as json_file:
        json.dump(tags, json_file, default=obj_dict, ensure_ascii=False)
    response.status_code = status.HTTP_201_CREATED
    return "OK - " + nimi + " lisätty tageihin"


@app.post('/tagit/{tagin_nimi}/{avainsana}/{aika}', summary='Lisää tagille avainsana')
async def create_tag(tagin_nimi: str, avainsana: str, aika: str, response: Response, user=Depends(get_current_user)):
    avainsana = avainsana + "?t=" + aika.lower()
    tagin_nimi = tagin_nimi.lower()
    check_tags()
    with open("tags.json") as f:
        tags = json.load(f)
    if tags[tagin_nimi] is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return "Tagia " + avainsana + " ei ole olemassa"
    if avainsana in tags[tagin_nimi]:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return "Avainsana " + avainsana + " on jo tagissa"
    tags[tagin_nimi].append(avainsana)
    with open("tags.json", 'w') as json_file:
        json.dump(tags, json_file, default=obj_dict, ensure_ascii=False)
    return "OK - " + avainsana + " lisätty tagiin: " + tagin_nimi


@app.delete('/tagit/{tagin_nimi}/{avainsana}/{aika}', summary='Lisää tagille avainsana')
async def delete_tag(tagin_nimi: str, avainsana: str, aika: str, response: Response, user=Depends(get_current_user)):
    avainsana = avainsana + "?t=" + aika.lower()
    tagin_nimi = tagin_nimi.lower()
    check_tags()
    with open("tags.json") as f:
        tags = json.load(f)
    if tags[tagin_nimi] is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return "Tagia " + avainsana + " ei ole olemassa"
    if avainsana in tags[tagin_nimi]:
        tags[tagin_nimi].remove(avainsana)
        with open("tags.json", 'w') as json_file:
            json.dump(tags, json_file, default=obj_dict, ensure_ascii=False)
        return "OK - " + avainsana + " poistettu tagista: " + tagin_nimi
    response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return "Tagia poistaessa tapahtui virhe"


@app.get('/tagit', summary='Listaa kaikki tagit')
async def get_tags():
    check_tags()
    data = json.load(open('tags.json', encoding='utf-8'))
    return json.dumps(data)


@app.get("/ehdotukset", summary="Listaa kaikki ehdotukset")
def get_suggestions():
    check_suggestions()
    suggestions = json.load(open('suggestions.json', encoding='utf-8'))
    return json.dumps(suggestions)


@app.post("/ehdotukset", summary="Lisää uuden ehdotuksen")
def create_suggestion(ehdotus: str, response: Response):
    check_suggestions()
    with open("suggestions.json") as f:
        suggestions = json.load(f)
    suggestions[ehdotus] = date.today().strftime("%d-%m-%Y")
    with open("suggestions.json", 'w') as json_file:
        json.dump(suggestions, json_file, default=obj_dict, ensure_ascii=False)
    response.status_code = status.HTTP_201_CREATED
    return "OK - " + ehdotus + " lisätty ehdotuksiin"


@app.get("/keskusteluohjelma", summary="Listaa aiheet hakusanan mukaan")
def hello(term: str):
    data = json.load(open('data.json', encoding='utf-8'))
    tags = json.load(open('tags.json', encoding='utf-8'))
    links = []
    tagged_ids = []
    for tag in tags:
        if tag == term:
            videos = tags[term]
            for i in range(1, len(videos)):
                tagged_ids.append(videos[i])
    for d in data:
        for c in d["chapters"]:
            chapter_id = d["videoId"] + "?t=" + str(c[0])
            if term in c[1]:
                link = [d["title"], c[1], "https://youtu.be/" + chapter_id]
                links.append(link)
            elif chapter_id in tagged_ids:
                link = [d["title"], c[1], "https://youtu.be/" + chapter_id]
                links.append(link)

    return json.dumps(links, ensure_ascii=False)