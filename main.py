from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

exec(open("videoRequester.py").read())


@app.get("/keskusteluohjelma")
def hello(term: str):

    data = json.load(open('data.json'))

    links = []
    for d in data:
        for c in d["chapters"]:
            if term in c[1]:
                link = [d["title"], c[1], "https://youtu.be/" + d["videoId"] + "?t=" + str(c[0])]
                links.append(link)

    return json.dumps(links)
