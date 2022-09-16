from fastapi import FastAPI, status, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from schemas import UserOut, UserAuth, TokenSchema
from deps import get_current_user
import json
from utils import (
    get_hashed_password,
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

#exec(open("videoRequester.py").read())


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


@app.get('/luoTagi', summary='Luo uusi tagi', response_model=UserOut)
async def get_me(user = Depends(get_current_user)):
    return user


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