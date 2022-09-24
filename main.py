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


def obj_dict(obj):
    return obj.__dict__


# exec(open("videoRequester.py").read())


@app.post('/kirjaudu', summary="Kirjaudu sisään", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
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
    json_file = open("users.json", "w")
    json_file.write(json_string)
    json_file.close()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@app.post('/tagit', summary='Luo uusi tagi')
async def create_tag(nimi: str, response: Response, user=Depends(get_current_user)):
    nimi = nimi.lower()
    if path.isfile("tags.json") is False:
        with open("tags.json", 'w') as f:
            json.dump({"piilotettu": [""]}, f)
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


@app.post('/tagit/{tagin_nimi}', summary='Lisää tagille avainsana')
async def create_tag(tagin_nimi: str, avainsana: str, response: Response, user=Depends(get_current_user)):
    avainsana = avainsana.lower()
    tagin_nimi = tagin_nimi.lower()
    print(avainsana)
    print(tagin_nimi)
    if path.isfile("tags.json") is False:
        with open("tags.json", 'w') as f:
            json.dump({"piilotettu": [""]}, f)
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


@app.get('/tagit', summary='Listaa kaikki tagit')
async def get_tags():
    data = json.load(open('tags.json', encoding='utf-8'))

    return json.dumps(data)


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
