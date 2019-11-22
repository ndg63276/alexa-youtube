#!/usr/bin/python

import sys, json, cgi
fs = cgi.FieldStorage()
youtube_id = fs.getvalue('id')
if youtube_id is None:
        youtube_id='9bZkp7q19f0'
video = fs.getvalue('video')
pytube = fs.getvalue('pytube')

print "Content-type:application/json"
print

saveout = sys.stdout
sys.stdout = open('/dev/null','a')

if pytube is None:
#       sys.path.append('/path/to/python/library/for/youtube_dl')
        import youtube_dl
        youtube_dl_properties = {}
        with youtube_dl.YoutubeDL(youtube_dl_properties) as ydl:
                yt_url = 'http://www.youtube.com/watch?v='+youtube_id
                info = ydl.extract_info(yt_url, download=False)
else:
#       sys.path.append('/path/to/python/library/for/pytube')
        from pytube import YouTube
        from pytube.exceptions import LiveStreamError
        try:
                yt=YouTube('https://www.youtube.com/watch?v='+youtube_id)
                if video is not None and video.lower() == 'video':
                        first_stream = yt.streams.filter(progressive=True).first()
                else:
                        first_stream = yt.streams.filter(only_audio=True, subtype='mp4').first()
                url = first_stream.url.replace(',','%2C')
                info = { 'is_live': False, 'url': url, 'title': yt.title }
        except LiveStreamError:
                info = { 'is_live': True, 'url': None, 'title': None }
        except:
                info = { 'is_live': False, 'url': None, 'title': None }

sys.stdout = saveout
print(json.dumps(info))
