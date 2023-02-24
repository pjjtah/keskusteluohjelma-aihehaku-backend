import os
# from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import schedule
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
from storage import upload_tags, download_tags, download_data, upload_data, upload_watches, upload_suggestions,\
    upload_users, download_suggestions, download_watches
from dotenv import load_dotenv
from videoRequester import get_videos
from datetime import date, datetime

load_dotenv()

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

# connect_str = os.environ['connect_str']
# container_name = os.environ['container_name']
# container_client = ContainerClient.from_connection_string(connect_str, container_name)


def obj_dict(obj):
    return obj.__dict__


def backup_tags():
    if path.isfile("tags.json"):
        upload_tags()
        '''
        with open("tags.json") as f:
            tags = json.load(f)
        date_time = datetime.now().strftime("%m-%d-%Y_%H-%M")
        with open("backups/tags" + date_time + ".json", 'w') as json_file:
            json.dump(tags, json_file, default=obj_dict, ensure_ascii=False)
        '''


# Run job every 6 hours
# schedule.every(3).hours.do(backup_tags)
schedule.every().day.do(get_videos)
schedule.every().day.do(upload_data)

# get_videos()


def check_tags():
    if path.isfile("tags.json") is False:
        download_tags()
        '''
        with open("tags.json", 'w') as f:
            json.dump({"piilotettu": [""], "ylapeukku": [""], "alapeukku": [""], "lit": [""]}, f)
        '''
    # schedule.run_pending()


def check_data():
    schedule.run_pending()
    if path.isfile("data.json") is False:
        download_data()


def check_suggestions():
    if path.isfile("suggestions.json") is False:
        download_suggestions()


def check_watches():
    if path.isfile("suggestions.json") is False:
        download_watches()


@app.post('/kirjaudu', summary="Kirjaudu sisään", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if path.isfile("users.json") is False:
        with open("users.json", 'w') as f:
            json.dump({"id": "087cb8b7-add0-45d3-9407-d0d99d26c253", "username": os.environ.get("_username"),
                       "password": os.environ.get("_password"),
                       "access_token": "", "refresh_token": ""}, f)
        upload_users()
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

    print(user['username'])
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
    with open("tags.json", encoding='utf-8') as f:
        tags = json.load(f)
    if nimi in tags:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return "Tagi " + nimi + " on jo olemassa"
    tags[nimi] = [nimi]
    with open("tags.json", 'w', encoding='utf-8') as json_file:
        json.dump(tags, json_file, default=obj_dict, ensure_ascii=False)
    upload_tags()
    response.status_code = status.HTTP_201_CREATED
    return "OK - " + nimi + " lisätty tageihin"


@app.post('/tagit/{tagin_nimi}/{avainsana}/{aika}', summary='Lisää tagille avainsana')
async def create_tag(tagin_nimi: str, avainsana: str, aika: str, response: Response, user=Depends(get_current_user)):
    avainsana = avainsana + "?t=" + aika.lower()
    tagin_nimi = tagin_nimi.lower()
    check_tags()
    with open("tags.json", encoding='utf-8') as f:
        tags = json.load(f)
    if tags[tagin_nimi] is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return "Tagia " + avainsana + " ei ole olemassa"
    if avainsana in tags[tagin_nimi]:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return "Avainsana " + tagin_nimi + " on jo tagissa"
    tags[tagin_nimi].append(avainsana)
    with open("tags.json", 'w', encoding='utf-8') as json_file:
        json.dump(tags, json_file, default=obj_dict, ensure_ascii=False)
    upload_tags()
    return "OK - " + avainsana + " lisätty tagiin: " + tagin_nimi


@app.delete('/tagit/{tagin_nimi}/{avainsana}/{aika}', summary='Poistaa tagilta avainsanan')
async def delete_tag(tagin_nimi: str, avainsana: str, aika: str, response: Response, user=Depends(get_current_user)):
    avainsana = avainsana + "?t=" + aika.lower()
    tagin_nimi = tagin_nimi.lower()
    check_tags()
    with open("tags.json", encoding='utf-8') as f:
        tags = json.load(f)
    if tags[tagin_nimi] is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return "Tagia " + avainsana + " ei ole olemassa"
    if avainsana in tags[tagin_nimi]:
        tags[tagin_nimi].remove(avainsana)
        with open("tags.json", 'w', encoding='utf-8') as json_file:
            json.dump(tags, json_file, default=obj_dict, ensure_ascii=False)
        upload_tags()
        return "OK - " + avainsana + " poistettu tagista: " + tagin_nimi
    response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return "Tagia poistaessa tapahtui virhe"


@app.delete('/tagit', summary='Poista tagi')
async def delete_tag(nimi: str, response: Response, user=Depends(get_current_user)):
    tagin_nimi = nimi
    check_tags()
    print(tagin_nimi)
    print(nimi)
    with open("tags.json", encoding='utf-8') as f:
        tags = json.load(f)
    if tags[tagin_nimi] is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return "Tagia " + tagin_nimi + " ei ole olemassa"
    if tagin_nimi in tags:
        tags.pop(tagin_nimi)
        with open("tags.json", 'w', encoding='utf-8') as json_file:
            json.dump(tags, json_file, default=obj_dict, ensure_ascii=False)
        return "OK - " + tagin_nimi + " poistettu tageista"
    response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return "Tagia poistaessa tapahtui virhe"


@app.get('/tagit', summary='Listaa kaikki tagit')
async def get_tags():
    check_tags()
    data = json.load(open('tags.json', encoding='iso-8859-1'))
    return json.dumps(data)


@app.get('/tagit/{videoId}', summary='Listaa kaikki videon tagit')
async def get_tags_by_videoId(videoId: str):
    check_tags()
    data = json.load(open('tags.json', encoding='utf-8'))
    selected = []
    for tag in data:
        for t in data[tag]:
            if videoId in t:
                selected.append(tag)
                break

    return json.dumps(selected)


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
    upload_suggestions()
    response.status_code = status.HTTP_201_CREATED
    return "OK - " + ehdotus + " lisätty ehdotuksiin"


'''
@app.get("/keskusteluohjelma", summary="Listaa aiheet hakusanan mukaan")
def hello(term: str):
    data = json.load(open('data.json', encoding='utf-8'))
    links = []
    for d in data:
        for c in d["chapters"]:
            if term in c[1]:
                link = [d["title"], c[1], "https://youtu.be/" + d["videoId"] + "?t=" + str(c[0])]
                links.append(link)

    return json.dumps(links, ensure_ascii=False)


'''


@app.get("/keskusteluohjelma", summary="Listaa aiheet hakusanan mukaan")
def hello(term: str):
    check_tags()
    check_data()
    data = json.load(open('data.json', encoding='utf-8'))
    tags = json.load(open('tags.json', encoding='"utf-8")'))
    if term == "":
        links = []
        for d in data:
            for c in d["chapters"]:
                if term in c[1]:
                    if d["videoId"] + "?t=" + str(c[0]) not in tags["piilotettu"]:
                        if "VLOG" in d["title"] or "EDUSKUNTAVAALIT" in d["title"]:
                            link = [d["title"], c[1], "https://youtu.be/" + d["videoId"] + "?t=" + str(c[0])]
                            links.append(link)
        return json.dumps(links, ensure_ascii=False)

    links = []
    tagged = []
    tagged_ids = []

    for tag in tags:
        if term in tag:
            tagged.append(tag)
    for tag in tagged:
        for t in tags[tag]:
            if t != tag:
                tagged_ids.append(t)
    for d in data:
        for c in d["chapters"]:
            print(c)
            print(term)
            if d["videoId"] + "?t=" + str(c[0]) in tagged_ids or term in c[1].lower():
                if "VLOG" in d["title"] or "EDUSKUNTAVAALIT" in d["title"]:
                    link = [d["title"], c[1], "https://youtu.be/" + d["videoId"] + "?t=" + str(c[0])]
                    links.append(link)
    return json.dumps(links, ensure_ascii=False)


@app.get("/keskusteluohjelmaAdmin", summary="Listaa aiheet hakusanan mukaan")
def hello(term: str):
    check_data()
    check_tags()
    data = json.load(open('data.json', encoding='utf-8'))
    if term == "":
        links = []
        for d in data:
            for c in d["chapters"]:
                if term in c[1]:
                    if "VLOG" in d["title"] or "EDUSKUNTAVAALIT" in d["title"]:
                        link = [d["title"], c[1], "https://youtu.be/" + d["videoId"] + "?t=" + str(c[0])]
                        links.append(link)
        return json.dumps(links, ensure_ascii=False)

    tags = json.load(open('tags.json', encoding='utf-8'))
    links = []
    tagged = []
    tagged_ids = []

    for tag in tags:
        if term in tag:
            tagged.append(tag)
    for tag in tagged:
        for t in tags[tag]:
            if t != tag:
                tagged_ids.append(t)
    for d in data:
        for c in d["chapters"]:
            if d["videoId"] + "?t=" + str(c[0]) in tagged_ids or term in c[1].lower():
                if "VLOG" in d["title"] or "EDUSKUNTAVAALIT" in d["title"]:
                    link = [d["title"], c[1], "https://youtu.be/" + d["videoId"] + "?t=" + str(c[0])]
                    links.append(link)
    return json.dumps(links, ensure_ascii=False)


@app.get("/katsottu/{videoId}", summary="Kasvattaa videon katsottu counteria yhdellä")
def increaseWatched(videoId: str, t: str):
    check_watches()
    with open("watches.json") as f:
        watches = json.load(f)
    if videoId + "?t=" + t in watches:
        watches[videoId + "?t=" + t] = watches[videoId + "?t=" + t] + 1
    else:
        watches[videoId + "?t=" + t] = 1
    with open("watches.json", 'w') as json_file:
        json.dump(watches, json_file, default=obj_dict, ensure_ascii=False)
    upload_watches()
    return "OK"


'''
@app.get("/vaihdaNimi/{videoId}", summary="Kasvattaa videon katsottu counteria yhdellä")
def changeName(videoId: str, newName: str):
    if path.isfile("nimet.json") is False:
        with open("nimet.json", 'w') as f:
            json.dump({"0": "0"}, f)
    with open("watches.json") as f:
        watches = json.load(f)
    if videoId + "?t=" + t in watches:
        watches[videoId + "?t=" + t] = watches[videoId + "?t=" + t] + 1
    else:
        watches[videoId + "?t=" + t] = 0
    with open("watches.json", 'w') as json_file:
        json.dump(watches, json_file, default=obj_dict, ensure_ascii=False)
    return "OK"
'''