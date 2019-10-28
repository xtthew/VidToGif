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
        v = requests.get(url+'DASH_480') #Try 480P Video
        v = requests.get(url+'DASH_360') if v.status_code == 403 else v #Try 360P Video
        v = requests.get(url+'DASH_240') if v.status_code == 403 else v #Try 240P Video
        if v.status_code == 403:
            return "Failed"
        vFile = open('video.mp4','wb')
        vFile.write(v.content)
        return 'video.mp4'

    def findVideo(self, userAgent):
        timeout = 3
        response = requests.get('https://reddit.com'+self.source+'.json', headers = {'User-agent': userAgent})
        for _ in range(timeout):
            if not response.status_code == 200:
                response = requests.get('https://reddit.com'+self.source+'.json', headers = {'User-agent': userAgent})
        if not response.status_code == 200:
            return "Failed"
        jsonData = json.loads(response.content)
        if self.searchJSON('id', jsonData):
            linkID = self.searchJSON('id', jsonData)
        elif self.searchJSON('fallback_url', jsonData):
            print("No 'id' tag")
            linkID = self.searchJSON('fallback_url', jsonData).split('/')[3]
        else:
            print("No 'fallback_url' tag")
        url = 'https://v.redd.it/'+linkID+'/'
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
                url = imgurDict['data']['link'] if status == 200 else "Failed"
        return url

    def cleanUp(self, gif):
        try:
            os.remove('video.gif')
            os.remove('video.mp4')
            os.remove('imgur.json')
            os.remove(gif)
        except Exception as e:
            print(e)

class Initialize:
    def __init__(self, userName, userAgent):
        self.userName = userName
        self.userAgent = userAgent
    
    def checkComments(self, commentID):
        sleep(10) # Time for comment to propagate
        timeout = 3
        response = requests.get('https://www.reddit.com/api/info.json?id=t1_'+commentID, headers = {'User-agent': self.userAgent})
        for _ in range(timeout):
            if not response.status_code == 200:
                response = requests.get('https://www.reddit.com/api/info.json?id=t1_'+commentID, headers = {'User-agent': self.userAgent})
        jsonData = json.loads(response.content)
        author = jsonData['data']['children'][0]['data']['author']
        return author
    
    def Run(self):
        try:
            reddit = praw.Reddit(self.userName)
            for mention in reddit.inbox.mentions(limit=25):
                if mention.new:
                    submission = reddit.submission(id=mention.submission)
                    video = Video(submission.permalink)
                    gif = Gif(video.findVideo(self.userAgent))
                    link = gif.makeGif(str(mention.submission))
                    try:
                        response = 'Sorry, I could not process your request. I gave up.\n\nI will try better in the future!\n\n^(I am a bot.)' if link == "Failed" else 'Here is a [Link]('+link+') to the GIF that you requested.\n\n Right now I only do the first 5 seconds.\n\n^(I am a bot.)'
                        author = self.checkComments(str(mention.reply(response)))
                        if not author == self.userName:
                            reddit.redditor(str(mention.author)).message('GIF Request', response+"\n\n *You are getting this message, because I am unable to comment in the subreddit you tagged me in.*")
                    except Exception as e:
                        print(e)
                    mention.mark_read()
        except Exception as e:
            print(e)

bot = Initialize('vidtogif', 'Linux:vidtogif:v0.0.1 (by u/xtthew)')

while True: 
    bot.Run()
    sleep(60)