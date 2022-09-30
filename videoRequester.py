import json
import os

import requests


class Video:
    videoId = ""
    title = ""
    chapters = ""


apiKey = os.environ.get('apikey')
videosResponse = requests.get("https://www.googleapis.com/youtube/v3/search?key=" + apiKey +
                              "&channelId=UCBHvy-pjrxS88ZqiJXS6Ydw&part="
                              "snippet,id&order=date&maxResults=50")

videoPages = [videosResponse.json()]
while "nextPageToken" in videoPages[len(videoPages)-1]:
    videosResponse = requests.get("https://www.googleapis.com/youtube/v3/search?key=" + apiKey +
                                  "&channelId=UCBHvy-pjrxS88ZqiJXS6Ydw&part="
                                  "snippet,id&order=date&maxResults=50&pageToken=" + videoPages[len(videoPages)-1]["nextPageToken"])
    videoPages.append(videosResponse.json())

jsonVideos = []

counter = 0

for videos in videoPages:
    for v in videos["items"]:
        if v['id']["kind"] == 'youtube#video':
            descriptionResponse = requests.get("https://www.googleapis.com/youtube/v3/videos?part=snippet&id="
                                               + v["id"]["videoId"] + "&key=" + apiKey)
            descriptions = descriptionResponse.json()
            video = Video()
            video.videoId = v["id"]["videoId"]
            video.title = descriptions["items"][0]["snippet"]["title"]
            chapters = []
            chaptersStarted = False
            for line in descriptions["items"][0]["snippet"]["description"].splitlines():
                if line[0:4] == "0:00":
                    chaptersStarted = True
                if chaptersStarted:
                    if line == "":
                        break
                    chap = line.split(" ", 1)
                    seconds = 0
                    time = chap[0].split(":")
                    if len(time) > 2:
                        seconds += int(time[0]) * 3600
                        seconds += int(time[1]) * 60
                        seconds += int(time[2])
                    if len(time) == 2:
                        seconds += int(time[0]) * 60
                        seconds += int(time[1])
                    chap[0] = seconds
                    chapters.append(chap)
                    counter += 1

            video.chapters = chapters
            jsonVideos.append(video)


def obj_dict(obj):
    return obj.__dict__


jsonString = json.dumps(jsonVideos, default=obj_dict, ensure_ascii=False)
jsonFile = open("data.json", "w")
jsonFile.write(jsonString)
jsonFile.close()
print(str(len(jsonVideos)) + " videota käyty läpi")
print("Yhteensä " + str(counter) + " pätkää")
