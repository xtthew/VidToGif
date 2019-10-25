#Reddit Video To GIF Bot
#FFMPEG Code Thanks To Collin Burger, Director of Content Engineering - GIPHY
#via https://engineering.giphy.com/how-to-make-gifs-with-ffmpeg/
import os, sys, json
import requests
import praw
from time import sleep

class Video:
    def __init__(self, source):
        self.source = source

    def searchJSON(self, searchTerm, di=None):
        for k in di:
            print(k)
            if isinstance(k, str) and (k.find('flair') > 0): #flair dicts throw off search
                pass
            elif k == searchTerm:
                return di[k]
            elif isinstance(k, dict):
                return self.searchJSON(searchTerm, k)
            elif isinstance(k, list):
                return self.searchJSON(searchTerm, k[0])
            elif isinstance(di[k], list) or isinstance(di[k], dict):
                if di[k]:
                    return self.searchJSON(searchTerm, di[k])
                else:
                    pass

    def dlVideo(self, url):
        cmd = "wget -t 2 "+url
        os.system(cmd)
        return 'video.mp4'

    def findVideo(self):
        os.system('wget https://reddit.com'+self.source+'.json -O video.json')
        jsonFile = open('video.json', 'r')
        jsonData = json.loads(jsonFile.read())
        if self.searchJSON('id', jsonData):
            linkID = self.searchJSON('id', jsonData)
        elif self.searchJSON('fallback_url', jsonData):
            print("No 'id' tag")
            linkID = self.searchJSON('fallback_url', jsonData).split('/')[3]
        else:
            print("No 'fallback_url' tag")
        url = 'v.redd.it/'+linkID+'/DASH_480 -O video.mp4'
        jsonFile.close()
        return self.dlVideo(url)


class Gif:
    def __init__(self,videoSource):
        self.videoSource = videoSource
    
    def makeGif(self,gifID):
        startTime = 0
        gifLength = 5 # Currently only makes gifs from first 5 seconds
        GIFout = 'video.gif'
        newGIF = gifID+'.gif'
        vidToGif = 'ffmpeg -y -ss '+str(startTime)+' -t '+str(gifLength)+' -i '+self.videoSource+" -filter_complex '[0:v] fps=12,scale=w=480:h=-1,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1' "+GIFout
        compressGif = 'convert '+GIFout+' -fuzz 5% -layers Optimize '+newGIF
        os.system(vidToGif)
        os.system(compressGif)
        url = self.upload(newGIF)
        self.cleanUp(newGIF)
        return url

    def upload(self, filename):
        status = 0
        timeout = 3
        uploadGIF = "curl --location --request POST 'https://api.imgur.com/3/image' --header 'Authorization: Client-ID c9a6efb3d7932fd' --form 'image=@"+filename+"' > imgur.json"
        for _ in range(timeout):
            if status != 200:
                os.system(uploadGIF)
                imgurJSON = open('imgur.json', 'r')
                imgurDict = json.loads(imgurJSON.read())
                status = imgurDict['status']
                print('Return Status: '+str(status))
                url = imgurDict['data']['link'] if status == 200 else "Failed"
        return url

    def cleanUp(self, gif):
        try:
            os.remove('video.gif')
            os.remove('video.mp4')
            os.remove('imgur.json')
            os.remove('video.json')
            os.remove(gif)
        except Exception as e:
            print(e)

class Initialize:
    def Run(self):
        reddit = praw.Reddit('vidtogif')
        for mention in reddit.inbox.mentions(limit=25):
            if mention.new:
                # banned subreddits: funny, trashy
                submission = reddit.submission(id=mention.submission)
                video = Video(submission.permalink)
                gif = Gif(video.findVideo())
                link = gif.makeGif(str(mention.submission))
                try:
                    if link == "Failed":
                        mention.reply('Sorry, I could not post the GIF to Imgur. I gave up.\n\nI will try better in the future!\n\n^(I am a bot.)')
                    else:
                        mention.reply('Here is a [Link]('+link+') to the GIF that you requested.\n\n Right now I only do the first 5 seconds.\n\n^(I am a bot.)')
                except Exception as e:
                    print(e)
                mention.mark_read()
                sleep(600) #Sleep for ten minutes if new account

bot = Initialize()

while True:
    bot.Run()
    sleep(60)