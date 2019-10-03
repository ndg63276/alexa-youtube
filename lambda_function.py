# -*- coding: utf-8 -*-
from __future__ import print_function
from os import environ
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from urllib2 import HTTPError
import logging
from random import shuffle, randint
from botocore.vendored import requests
import re
from time import time
import json
from datetime import datetime
from dateutil import tz
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
DEVELOPER_KEY=environ['DEVELOPER_KEY']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
from strings import *
strings = strings_en

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_cardless_speechlet_response(output, reprompt_text, should_end_session, speech_type='PlainText'):
    text_or_ssml = 'text'
    if speech_type == 'SSML':
        text_or_ssml = 'ssml'
    return {
        'outputSpeech': {
            'type': speech_type,
            text_or_ssml: output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_audio_or_video_response(title, output, should_end_session, url, token, offsetInMilliseconds=0):
    if video_or_audio == [True,'video']:
        return build_video_response(title, output, url)
    else:
        return build_audio_speechlet_response(title, output, should_end_session, url, token, offsetInMilliseconds=0)

 
def build_audio_speechlet_response(title, output, should_end_session, url, token, offsetInMilliseconds=0):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'directives': [{
            'type': 'AudioPlayer.Play',
            'playBehavior': 'REPLACE_ALL',
            'audioItem': {
                'stream': {
                    'token': str(token),
                    'url': url,
                    'offsetInMilliseconds': offsetInMilliseconds
                }
            }
        }],
        'shouldEndSession': should_end_session
    }


def build_cardless_audio_speechlet_response(output, should_end_session, url, token, offsetInMilliseconds=0):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'directives': [{
            'type': 'AudioPlayer.Play',
            'playBehavior': 'REPLACE_ALL',
            'audioItem': {
                'stream': {
                    'token': str(token),
                    'url': url,
                    'offsetInMilliseconds': offsetInMilliseconds
                }
            }
        }],
        'shouldEndSession': should_end_session
    }


def build_audio_enqueue_response(should_end_session, url, previous_token, next_token, playBehavior='ENQUEUE'):
    to_return = {
        'directives': [{
            'type': 'AudioPlayer.Play',
            'playBehavior': playBehavior,
            'audioItem': {
                'stream': {
                    'token': str(next_token),
                    'url': url,
                    'offsetInMilliseconds': 0
                }
            }
        }],
        'shouldEndSession': should_end_session
    }
    if playBehavior == 'ENQUEUE':
        to_return['directives'][0]['audioItem']['stream']['expectedPreviousToken'] = str(previous_token)
    return to_return


def build_cancel_speechlet_response(title, output, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'directives': [{
            'type': 'AudioPlayer.ClearQueue',
            'clearBehavior' : "CLEAR_ALL"
        }],
        'shouldEndSession': should_end_session
    }


def build_stop_speechlet_response(output, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'directives': [{
            'type': 'AudioPlayer.Stop'
        }],
        'shouldEndSession': should_end_session
    }


def build_short_speechlet_response(output, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'shouldEndSession': should_end_session
    }


def build_response(speechlet_response, sessionAttributes={}):
    return {
        'version': '1.0',
        'sessionAttributes': sessionAttributes,
        'response': speechlet_response
    }

def build_video_response(title, output, url):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'directives': [{
            'type': 'VideoApp.Launch',
            'videoItem': {
                'source': url,
                'metadata': {
                    'title': title,
                }
            }
        }]
    }

# --------------- Main handler ------------------

def lambda_handler(event, context):
    if 'expires' in environ and int(datetime.strftime(datetime.now(),'%Y%m%d')) > int(environ['expires']):
        return skill_expired()
    global strings
    if event['request']['locale'][0:2] == 'fr':
        strings = strings_fr
    elif event['request']['locale'][0:2] == 'it':
        strings = strings_it
    elif event['request']['locale'][0:2] == 'de':
        strings = strings_de
    elif event['request']['locale'][0:2] == 'es':
        strings = strings_es
    elif event['request']['locale'][0:2] == 'ja':
        strings = strings_ja
    else:
        strings = strings_en
    global video_or_audio
    video_or_audio = [False, 'audio']
    if 'VideoApp' in event['context']['System']['device']['supportedInterfaces']:
        video_or_audio[0] = True
        if event['request']['type'] == "IntentRequest":
            if event['request']['intent']['name'] == 'PlayOneIntent':
                video_or_audio[1] = 'video'
    if event['request']['type'] == "LaunchRequest":
        return get_welcome_response(event)
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event)
    elif event['request']['type'] == "SessionEndedRequest":
        logger.info("on_session_ended")
    elif event['request']['type'].startswith('AudioPlayer'):
        return handle_playback(event)
        
# --------------- Events ------------------

def on_intent(event):
    intent_name = event['request']['intent']['name']
    # Dispatch to your skill's intent handlers
    search_intents = ["SearchIntent", "PlayOneIntent", "PlaylistIntent", "SearchMyPlaylistsIntent", "ShuffleMyPlaylistsIntent", "ChannelIntent", "ShuffleIntent", "ShufflePlaylistIntent", "ShuffleChannelIntent", "PlayMyLatestVideoIntent"]
    if intent_name in search_intents:
        return search(event)
    elif intent_name == 'NextPlaylistIntent':
        return next_playlist(event)
    elif intent_name == 'SkipForwardIntent':
        return skip_by(event, 1)
    elif intent_name == 'SkipBackwardIntent':
        return skip_by(event, -1)
    elif intent_name == 'SkipToIntent':
        return skip_to(event)
    elif intent_name == 'SayTimestampIntent':
        return say_timestamp(event)
    elif intent_name == 'AutoplayOffIntent':
        return change_mode(event, 'a', 0)
    elif intent_name == 'AutoplayOnIntent':
        return change_mode(event, 'a', 1)
    elif intent_name == "AMAZON.YesIntent":
        return yes_intent(event)
    elif intent_name == "AMAZON.NoIntent":
        return do_nothing()
    elif intent_name == "AMAZON.HelpIntent":
        return get_help()
    elif intent_name == "AMAZON.CancelIntent":
        return do_nothing()
    elif intent_name == "AMAZON.PreviousIntent":
        return skip_action(event, -1)
    elif intent_name == "AMAZON.NextIntent":
        return skip_action(event, 1)
    elif intent_name == "AMAZON.ShuffleOnIntent":
        return change_mode(event, 's', 1)
    elif intent_name == "AMAZON.ShuffleOffIntent":
        return change_mode(event, 's', 0)
    elif intent_name == "AMAZON.ResumeIntent":
        return resume(event)
    elif intent_name == "AMAZON.RepeatIntent" or intent_name == "NowPlayingIntent":
        return say_video_title(event)
    elif intent_name == "AMAZON.LoopOnIntent":
        return change_mode(event, 'l', 1)
    elif intent_name == "AMAZON.LoopOffIntent":
        return change_mode(event, 'l', 0)
    elif intent_name == "AMAZON.StartOverIntent":
        return start_over(event)
    elif intent_name == "AMAZON.StopIntent" or intent_name == "AMAZON.PauseIntent":
        return stop()
    elif intent_name == "PlayMoreLikeThisIntent":
        return play_more_like_this(event)
    else:
        raise ValueError("Invalid intent")
        
def handle_playback(event):
    request = event['request']
    if request['type'] == 'AudioPlayer.PlaybackStarted':
        return started(event)
    elif request['type'] == 'AudioPlayer.PlaybackFinished':
        return finished(event)
    elif request['type'] == 'AudioPlayer.PlaybackStopped':
        return stopped(event)
    elif request['type'] == 'AudioPlayer.PlaybackNearlyFinished':
        return nearly_finished(event)
    elif request['type'] == 'AudioPlayer.PlaybackFailed':
        return failed(event)

# --------------- Functions that control the skill's behavior ------------------

def get_headers(event):
    if 'apiAccessToken' in event['context']['System']:
        apiAccessToken = event['context']['System']['apiAccessToken']
        headers = {
        'Authorization': 'Bearer '+apiAccessToken,
        'Content-Type': 'application/json'
        }
        return headers
    else:
        logger.info('apiAccessToken not found')
        return False

def create_list(event, list_title):
    headers = get_headers(event)
    if not headers:
        return False
    data = {
        "name": list_title,
        "state": "active"
    }
    url = event['context']['System']['apiEndpoint'] + '/v2/householdlists/'
    r = requests.post(url, headers=headers, data=json.dumps(data))
    if r.status_code == 201:
        logger.info('List created')
        return True
    elif r.status_code == 409:
        logger.info('List already exists')
        return True
    elif r.status_code == 403:
        logger.info('List permissions not granted')
        return False
    else:
        logger.info(r.status_code)
        logger.info(r.json())
        return True

def get_list_id(event, list_title):
    headers = get_headers(event)
    if headers:
        url = event['context']['System']['apiEndpoint'] + '/v2/householdlists/'
        r = requests.get(url, headers=headers)
        try:
            lists = r.json()['lists']
        except:
            return None
        for list in lists:
            if list['name'] == list_title and list['state'] == 'active':
                return list['listId']
    return None

def read_list_item(event, listId):
    items = get_list(event, listId)
    if items is not None and len(items) > 0:
        return items[0]['id'], items[0]['value'], items[0]['version']
    return None, None, None

def update_list_item(event, listId, itemId, itemValue, itemVersion, itemStatus='completed'):
    headers = get_headers(event)
    if headers:
        data = {
            "value": itemValue,
            "status": itemStatus,
            "version": itemVersion
        }
        url = event['context']['System']['apiEndpoint'] + '/v2/householdlists/'+listId+'/items/'+itemId
        r = requests.put(url, headers=headers, data=json.dumps(data))
        logger.info(r.json())

def create_list_item(event, listId, title):
    headers = get_headers(event)
    if headers:
        timestamp = event['request']['timestamp']
        utc = datetime.strptime(timestamp,'%Y-%m-%dT%H:%M:%SZ')
        from_zone = tz.tzutc()
        timezone = get_time_zone(event)
        if type(timezone) != unicode:
            timezone = 'Europe/London'
            if event['request']['locale'] in locales:
                timezone = locales[event['request']['locale']]
        to_zone = tz.gettz(timezone)
        utc = utc.replace(tzinfo=from_zone)
        local = utc.astimezone(to_zone)
        the_date = local.strftime('%b %d %Y %H:%M:%S')
        data = {
            "value": the_date+' '+title,
            "status": "active"
        }
        url = event['context']['System']['apiEndpoint'] + '/v2/householdlists/'+listId+'/items/'
        r = requests.post(url, headers=headers, data=json.dumps(data))

def get_list(event, listId):
    headers = get_headers(event)
    if headers:
        url = event['context']['System']['apiEndpoint'] + '/v2/householdlists/'+listId+'/active/'
        r = requests.get(url, headers=headers)
        if 'items' in r.json():
            return r.json()['items']
    return None

def trim_list(event, listId):
    items = get_list(event, listId)
    if items is not None:
        maxLength = 90
        for item in items[maxLength:]:
            itemId = item['id']
            delete_list_item(event, listId, itemId)

def delete_list_item(event, listId, itemId):
    headers = get_headers(event)
    if headers:
        url = event['context']['System']['apiEndpoint'] + '/v2/householdlists/'+listId+'/items/'+itemId
        r = requests.delete(url, headers=headers)

def add_to_list(event, title):
    listId = get_list_id(event, 'YouTube')
    logger.info(listId)
    if listId is not None:
        create_list_item(event, listId, title)
        logger.info('Created item')
        trim_list(event, listId)

def get_welcome_response(event):
    list_created = create_list(event, 'YouTube')
    speech_output = strings['welcome1']
    reprompt_text = strings['welcome2']
    should_end_session = False
    if event['request']['locale'] == 'en-GB' and 'PLAY_ADVERT' in environ and randint(1,10) == 10:
        advert1 = '<voice name="Brian"><prosody rate="fast">Do you want cheaper energy? '
        advert2 = 'Go to <emphasis level="strong">bulb</emphasis>.co.uk/refer/<break time="0.1s"/>'
        advert3 = 'mark<break time="0.1s"/><say-as interpret-as="digits">7441</say-as>, and when you join, you\'ll get £50 of credit.</prosody></voice> '
        speech_output = advert1 + advert2 + advert3 + speech_output
        userId = event['context']['System']['user']['userId']
        payload = {'value1': userId}
        r = requests.get(environ['PLAY_ADVERT'], params=payload)
    speech_output = '<speak>' + speech_output + '</speak>'
    return build_response(build_cardless_speechlet_response(speech_output, reprompt_text, should_end_session, 'SSML'))
        
def get_help():
    speech_output = strings['help']
    card_title = 'Youtube Help'
    should_end_session = False
    return build_response(build_speechlet_response(card_title, speech_output, None, should_end_session))
            
def illegal_action():
    speech_output = strings['illegal']
    should_end_session = True
    return build_response(build_short_speechlet_response(speech_output, should_end_session))
        
def do_nothing():
    return build_response({})

def video_search(query, relatedToVideoId=None):
    try:
        search_response = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=50,
            relatedToVideoId=relatedToVideoId,
            type='video'
            ).execute()
    except HttpError as err:
        if json.loads(err.content.decode('utf-8'))['error']['code'] == 403:
            return False, "Sorry, this skill has hit it's usage limit for today. Please consider deploying the skill yourself for unlimited use"
        else:
            return False, "Sorry, there was a problem with the Youtube API key"
    videos = []
    for search_result in search_response.get('items', []):
        if 'videoId' in search_result['id']:
            videos.append(search_result['id']['videoId'])
    return videos, ""

def playlist_search(query, sr, do_shuffle='0'):
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=10,
        type='playlist'
        ).execute()
    for playlist in range(sr, len(search_response.get('items'))):
        if 'playlistId' in search_response.get('items')[playlist]['id']:
            playlist_id = search_response.get('items')[playlist]['id']['playlistId']
            break
    sr = playlist
    logger.info('Playlist info: https://www.youtube.com/playlist?list='+playlist_id)
    playlist_title = search_response.get('items')[sr]['snippet']['title']
    videos = []
    data={'nextPageToken':''}
    while 'nextPageToken' in data and len(videos) < 200:
        next_page_token = data['nextPageToken']
        data = youtube.playlistItems().list(part='snippet',maxResults=50,playlistId=playlist_id,pageToken=next_page_token).execute()
        for item in data['items']:
            try:
                videos.append(item['snippet']['resourceId']['videoId'])
            except:
                pass
    if do_shuffle == '1':
        shuffle(videos)
    return videos[0:50], playlist_title, sr

def my_playlists_search(query, sr, do_shuffle='0'):
    channel_id = None
    playlist_id = None
    if 'MY_CHANNEL_ID' in environ:
        channel_id = environ['MY_CHANNEL_ID']
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=10,
        type='playlist',
        channelId=channel_id
        ).execute()
    for playlist in range(sr, len(search_response.get('items'))):
        if 'playlistId' in search_response.get('items')[playlist]['id']:
            playlist_id = search_response.get('items')[playlist]['id']['playlistId']
            break
    if playlist_id is None:
        return [], None, 0
    sr = playlist
    logger.info('Playlist info: https://www.youtube.com/playlist?list='+playlist_id)
    playlist_title = search_response.get('items')[sr]['snippet']['title']
    videos = []
    data={'nextPageToken':''}
    while 'nextPageToken' in data and len(videos) < 200:
        next_page_token = data['nextPageToken']
        data = youtube.playlistItems().list(part='snippet',maxResults=50,playlistId=playlist_id,pageToken=next_page_token).execute()
        for item in data['items']:
            try:
                videos.append(item['snippet']['resourceId']['videoId'])
            except:
                pass
    if do_shuffle == '1':
        shuffle(videos)
    return videos[0:50], playlist_title, sr

def my_latest_video():
    channel_id = None
    if 'MY_CHANNEL_ID' in environ:
        channel_id = environ['MY_CHANNEL_ID']
    if channel_id is None:
        return build_response(build_short_speechlet_response('You do not have a channel id set', True))
    search_response = youtube.search().list(
        part='id,snippet',
        maxResults=50,
        type='video',
        order='date',
        channelId=channel_id
        ).execute()
    videos = []
    for search_result in search_response.get('items', []):
        if 'videoId' in search_result['id']:
            videos.append(search_result['id']['videoId'])
    return videos

def channel_search(query, sr, do_shuffle='0'):
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=10,
        type='channel'
        ).execute()
    playlist_id = search_response.get('items')[sr]['id']['channelId']
    playlist_title = search_response.get('items')[sr]['snippet']['title']
    data={'nextPageToken':''}
    videos = []
    while 'nextPageToken' in data and len(videos) < 200:
        next_page_token = data['nextPageToken']
        data = youtube.search().list(part='snippet',maxResults=50,channelId=playlist_id,pageToken=next_page_token).execute()
        for item in data['items']:
            try:
                videos.append(item['id']['videoId'])
            except:
                pass
    if do_shuffle == '1':
        shuffle(videos)
    return videos[0:50], playlist_title

def get_url_and_title(id):
    if 'youtube_dl' in environ and environ['youtube_dl'].lower() == 'true':
        return get_url_and_title_youtube_dl(id)
    else:
        return get_url_and_title_pytube(id)

def get_url_and_title_youtube_dl(id):
    import youtube_dl
    logger.info('Getting youtube-dl url for https://www.youtube.com/watch?v='+id)
    youtube_dl_properties = {}
    if 'proxy_enabled' in environ and 'proxy' in environ and environ['proxy_enabled'].lower() == 'true':
        youtube_dl_properties['proxy'] = environ['proxy']
    try:
        with youtube_dl.YoutubeDL(youtube_dl_properties) as ydl:
            yt_url = 'http://www.youtube.com/watch?v='+id
            info = ydl.extract_info(yt_url, download=False)
    except HTTPError as e:
        logger.info('HTTPError code '+str(e.code))
        return False,False
    except:
        logger.info('Other ytdl error')
        return False,False
    if info['is_live'] == True:
        video_or_audio[1] = 'video'
        return info['url'], info['title']
        #return get_live_video_url_and_title(id) # Test both of these
    for f in info['formats']:
        if video_or_audio[1] == 'audio' and f['vcodec'] == 'none' and f['ext'] == 'm4a':
            return f['url'], info['title'] # Test this
        if video_or_audio[1] == 'video' and f['vcodec'] != 'none' and f['acodec'] != 'none':
            return f['url'], info['title'] # Test this
    logger.info('Unable to get URL for '+id)
    return None, None

def get_url_and_title_pytube(id):
    from pytube import YouTube
    from pytube.exceptions import LiveStreamError
    proxy_list = {}
    if 'proxy_enabled' in environ and 'proxy' in environ and environ['proxy_enabled'] == 'true':
        proxy_list = {'https': environ['proxy']}
    logger.info('Getting pytube url for https://www.youtube.com/watch?v='+id)
    try:
        yt=YouTube('https://www.youtube.com/watch?v='+id, proxies = proxy_list)
    except LiveStreamError:
        logger.info(id+' is a live video')
        return get_live_video_url_and_title(id)
    except HTTPError as e:
        logger.info('HTTPError code '+str(e.code))
        return False,False
    except:
        logger.info('Unable to get URL for '+id)
        return None,None
    if video_or_audio[1] == 'video':
        first_stream = yt.streams.filter(progressive=True).first()
    else:
        first_stream = yt.streams.filter(only_audio=True, subtype='mp4').first()
    logger.info(first_stream.url)
    return first_stream.url, yt.title

def get_live_video_url_and_title(id):
    logger.info('Live video?')
    title = 'live video'
    try:
        u = 'https://www.youtube.com/watch?v='+id
        r = requests.get(u)
        a = re.search('https:[%\_\-\\\/\.a-z0-9]+m3u8', r.text, re.I)
        url = a.group().replace('\\/','/')
        logger.info(url)
        t = re.search('<title>(.+) - youtube</title>', r.text, re.I)
        if t:
            title = t.groups()[0]
        video_or_audio[1] = 'video'
        return url, title
    except:
        logger.info('Unable to get m3u8')
        return None, None

def yes_intent(event):
    session = event['session']
    sessionAttributes = session.get('attributes')
    if not sessionAttributes or 'intent' not in sessionAttributes or 'sr' not in sessionAttributes:
        return build_response(build_cardless_speechlet_response(strings['gonewrong'], None, True))
    intent = sessionAttributes['intent']
    session['attributes']['sr'] = sessionAttributes['sr'] + 1
    return search(event)

def next_playlist(event):
    intent = event['request']['intent']
    session = event['session']
    logger.info(intent)
    if 'token' not in event['context']['AudioPlayer']:
        speech_output = strings['nothingplaying']
        return build_response(build_short_speechlet_response(speech_output, True))
    current_token = event['context']['AudioPlayer']['token']
    playlist = convert_token_to_dict(current_token)
    if 'sr' not in playlist or 'query' not in playlist:
        return build_response(build_cardless_speechlet_response(strings['gonewrong'], None, True))
    if 'attributes' not in session:
        session['attributes'] = {}
    session['attributes']['sr'] = int(playlist['sr']) + 1
    session['attributes']['query'] = playlist['query']
    return search(event)

def search(event):
    session = event['session']
    intent = event['request']['intent']
    startTime = time()
    query = ''
    if 'slots' in intent and 'query' in intent['slots']:
        query = intent['slots']['query']['value']
        logger.info('Looking for: ' + query)
    should_end_session = True
    intent_name = intent['name']
    playlist_title = None
    sessionAttributes = session.get('attributes')
    if not sessionAttributes:
        sessionAttributes={'sr':0, 'intent':intent}
    if 'query' in sessionAttributes:
        query = sessionAttributes['query'].replace('_',' ')
    sr = sessionAttributes['sr']
    playlist = {}
    playlist['s'] = '0'
    playlist['sr'] = sr
    playlist['a'] = '1'
    playlist['i'] = intent_name.replace('Intent','')
    if intent_name == "PlayOneIntent":
        playlist['a'] = '0'
    playlist['query'] = query.replace(' ','_')
    if intent_name == "ShuffleIntent" or intent_name == "ShufflePlaylistIntent" or intent_name == "ShuffleChannelIntent" or intent_name == "ShuffleMyPlaylistsIntent":
        playlist['s'] = '1'
    playlist['l'] = '0'
    if intent_name == "PlaylistIntent" or intent_name == "ShufflePlaylistIntent" or intent_name == "NextPlaylistIntent":
        videos, playlist_title, playlist['sr'] = playlist_search(query, sr, playlist['s'])
        playlist_channel_video = strings['playlist']
    elif intent_name == "SearchMyPlaylistsIntent" or intent_name == "ShuffleMyPlaylistsIntent":
        videos, playlist_title, playlist['sr'] = my_playlists_search(query, sr, playlist['s'])
        playlist_channel_video = strings['playlist']
    elif intent_name == "ChannelIntent" or intent_name == "ShuffleChannelIntent":
        videos, playlist_title = channel_search(query, sr, playlist['s'])
        playlist_channel_video = strings['channel']
    elif intent_name == "PlayMyLatestVideoIntent":
        videos = my_latest_video()
        playlist_channel_video = strings['video']
    else:
        videos, errorMessage = video_search(query)
        playlist_channel_video = strings['video']
    if videos == False:
        return build_response(build_cardless_speechlet_response(errorMessage, None, True))
    if videos == []:
        return build_response(build_cardless_speechlet_response(strings['novideo'], None, True))
    next_url = None
    for i,id in enumerate(videos):
        if playlist_channel_video != strings['video'] and time() - startTime > 8:
            return build_response(build_cardless_speechlet_response(playlist_channel_video+" "+playlist_title+" " + strings['notworked'], None, False), sessionAttributes)
        playlist['v'+str(i)]=id
        if next_url is None:
            playlist['p'] = i
            next_url, title = get_url_and_title(id)
    if next_url == False:
        return build_response(build_short_speechlet_response('This skill is being throttled by YouTube, please try again later', True))
    next_token = convert_dict_to_token(playlist)
    if playlist_title is None:
        speech_output = strings['playing'] + ' ' + title
    else:
        speech_output = strings['playing'] + ' ' + playlist_title
    card_title = "Youtube"
    return build_response(build_audio_or_video_response(card_title, speech_output, should_end_session, next_url, next_token))

def stop():
    should_end_session = True
    speech_output = strings['pausing']
    return build_response(build_stop_speechlet_response(speech_output, should_end_session))

def nearly_finished(event):
    should_end_session = True
    current_token = event['request']['token']
    skip = 1
    next_url, next_token, title = get_next_url_and_token(current_token, skip)
    if title is None:
        playlist = convert_token_to_dict(next_token)
        if playlist['i'] != 'ShuffleMyPlaylists':
            return do_nothing()
        videos, playlist_title, playlist['sr'] = my_playlists_search(playlist['query'], int(playlist['sr']), playlist['s'])
        for i,id in enumerate(videos):
            playlist['v'+str(i)]=id
            if next_url is None:
                playlist['p'] = i
                next_url, title = get_url_and_title(id)
        next_token = convert_dict_to_token(playlist)
    if next_url == False:
        return do_nothing()
    return build_response(build_audio_enqueue_response(should_end_session, next_url, current_token, next_token))

def play_more_like_this(event):
    should_end_session = True
    if 'AudioPlayer' not in event['context'] or 'token' not in event['context']['AudioPlayer']:
        speech_output = strings['nothingplaying']
        return build_response(build_short_speechlet_response(speech_output, True))
    current_token = event['context']['AudioPlayer']['token']
    playlist = convert_token_to_dict(current_token)
    now_playing = playlist['p']
    now_playing_id = playlist['v'+now_playing]
    videos, errorMessage = video_search(None, now_playing_id)
    if videos == False:
        return build_response(build_short_speechlet_response(errorMessage, True))
    next_url = None
    for i,id in enumerate(videos):
        playlist['v'+str(i)]=id
        if next_url is None:
            playlist['p'] = i
            next_url, title = get_url_and_title(id)
    if next_url == False:
        return build_response(build_short_speechlet_response('This skill is being throttled by YouTube, please try again later', True))
    next_token = convert_dict_to_token(playlist)
    speech_output = strings['playing']+' '+title
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, next_token))

def skip_action(event, skip):
    logger.info("event:")
    logger.info(event)
    logger.info("context:")
    logger.info(event['context'])
    should_end_session = True
    current_token = event['context']['AudioPlayer']['token']
    next_url, next_token, title = get_next_url_and_token(current_token, skip)
    if title is None:
        playlist = convert_token_to_dict(next_token)
        if playlist['i'] != 'ShuffleMyPlaylists':
            speech_output = strings['nomoreitems']
            return build_response(build_short_speechlet_response(speech_output, should_end_session))
        videos, playlist_title, playlist['sr'] = my_playlists_search(playlist['query'], int(playlist['sr']), playlist['s'])
        for i,id in enumerate(videos):
            playlist['v'+str(i)]=id
            if next_url is None:
                playlist['p'] = i
                next_url, title = get_url_and_title(id)
        next_token = convert_dict_to_token(playlist)
    if next_url == False:
        return build_response(build_short_speechlet_response('This skill is being throttled by YouTube, please try again later', True))
    speech_output = strings['playing']+' '+title
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, next_token))

def skip_by(event, direction):
    intent = event['request']['intent']
    logger.info(intent)
    if 'token' not in event['context']['AudioPlayer']:
        speech_output = strings['nothingplaying']
        return build_response(build_short_speechlet_response(speech_output, True))
    if 'slots' not in intent:
        speech_output = strings['sorryskipby']
        return build_response(build_short_speechlet_response(speech_output, True))
    if 'hours' in intent['slots'] and 'value' in intent['slots']['hours']:
        try:
            hours = int(intent['slots']['hours']['value'])
        except:
            hours = 0
    else:
        hours = 0
    if 'minutes' in intent['slots'] and 'value' in intent['slots']['minutes']:
        try:
            minutes = int(intent['slots']['minutes']['value'])
        except:
            minutes = 0
    else:
        minutes = 0
    if 'seconds' in intent['slots'] and 'value' in intent['slots']['seconds']:
        try:
            seconds = int(intent['slots']['seconds']['value'])
        except:
            seconds = 0
    else:
        seconds = 0
    if hours == 0 and minutes == 0 and seconds == 0:
        speech_output = strings['sorryskipby']
        return build_response(build_short_speechlet_response(speech_output, True))
    current_offsetInMilliseconds = event['context']['AudioPlayer']['offsetInMilliseconds']
    skip_by_offsetInMilliseconds = direction * (hours * 3600000 + minutes * 60000 + seconds * 1000)
    return resume(event, current_offsetInMilliseconds+skip_by_offsetInMilliseconds)

def skip_to(event):
    intent = event['request']['intent']
    logger.info(intent)
    if 'token' not in event['context']['AudioPlayer']:
        speech_output = strings['nothingplaying']
        return build_response(build_short_speechlet_response(speech_output, True))
    if 'slots' not in intent:
        speech_output = strings['sorryskipto']
        return build_response(build_short_speechlet_response(speech_output, True))
    if 'hours' in intent['slots'] and 'value' in intent['slots']['hours']:
        try:
            hours = int(intent['slots']['hours']['value'])
        except:
            hours = 0
    else:
        hours = 0
    if 'minutes' in intent['slots'] and 'value' in intent['slots']['minutes']:
        try:
            minutes = int(intent['slots']['minutes']['value'])
        except:
            minutes = 0
    else:
        minutes = 0
    if 'seconds' in intent['slots'] and 'value' in intent['slots']['seconds']:
        try:
            seconds = int(intent['slots']['seconds']['value'])
        except:
            seconds = 0
    else:
        seconds = 0
    if hours == 0 and minutes == 0 and seconds == 0:
        speech_output = strings['sorryskipto']
        return build_response(build_short_speechlet_response(speech_output, True))
    offsetInMilliseconds = hours * 3600000 + minutes * 60000 + seconds * 1000
    return resume(event, offsetInMilliseconds)

def resume(event, offsetInMilliseconds=None):
    if 'token' not in event['context']['AudioPlayer']:
        return get_welcome_response(event)
    current_token = event['context']['AudioPlayer']['token']
    should_end_session = True
    speech_output = strings['ok']
    if offsetInMilliseconds is None:
        speech_output = strings['resuming']
        offsetInMilliseconds = event['context']['AudioPlayer']['offsetInMilliseconds']
    next_url, next_token, title = get_next_url_and_token(current_token, 0)
    if title is None:
        speech_output = strings['noresume']
        return build_response(build_short_speechlet_response(speech_output, should_end_session))
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, current_token, offsetInMilliseconds))

def change_mode(event, mode, value):
    current_token = event['context']['AudioPlayer']['token']
    should_end_session = True
    playlist = convert_token_to_dict(current_token)
    playlist[mode] = str(value)
    current_token = convert_dict_to_token(playlist)
    speech_output = strings['ok']
    offsetInMilliseconds = event['context']['AudioPlayer']['offsetInMilliseconds']
    next_url, next_token, title = get_next_url_and_token(current_token, 0)
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, current_token, offsetInMilliseconds))

def start_over(event):
    current_token = event['context']['AudioPlayer']['token']
    should_end_session = True
    next_url, next_token, title = get_next_url_and_token(current_token, 0)
    if title is None:
        speech_output = strings['novideo']
        return build_response(build_short_speechlet_response(speech_output, should_end_session))
    speech_output = strings['playing']+" " + title    
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, next_token))

def say_video_title(event):
    should_end_session = True
    if 'token' in event['context']['AudioPlayer']:
        current_token = event['context']['AudioPlayer']['token']
        next_url, next_token, title = get_next_url_and_token(current_token, 0)
        if title is None:
            speech_output = strings['notitle']
        else:
            speech_output = strings['nowplaying']+" "+title
    else:
        speech_output = strings['nothingplaying']
    return build_response(build_short_speechlet_response(speech_output, should_end_session))

def say_timestamp(event):
    should_end_session = True
    if 'offsetInMilliseconds' in event['context']['AudioPlayer']:
        current_offsetInMilliseconds = int(event['context']['AudioPlayer']['offsetInMilliseconds'])
        hours = current_offsetInMilliseconds / 3600000
        minutes = (current_offsetInMilliseconds - hours*3600000) / 60000
        seconds = (current_offsetInMilliseconds - hours*3600000 - minutes*60000) / 1000
        speech_output = strings['currentposition']
        if hours >= 2:
            speech_output += ' ' + str(hours) + ' ' + strings['hours'] + ', '
        elif hours == 1:
            speech_output += ' ' + str(hours) + ' ' + strings['hour'] + ', '
        if minutes == 1:
            speech_output += ' ' + str(minutes) + ' ' + strings['minute'] + ', '
        else:
            speech_output += ' ' + str(minutes) + ' ' + strings['minutes'] + ', '
        if seconds == 1:
            speech_output += ' ' + str(seconds) + ' ' + strings['second'] + ', '
        else:
            speech_output += ' ' + str(seconds) + ' ' + strings['seconds'] + ', '
    else:
        speech_output = strings['nothingplaying']
    return build_response(build_short_speechlet_response(speech_output, should_end_session))
    
def convert_token_to_dict(token):
    pi=token.split('&')
    playlist={}
    for i in pi:
        key=i.split('=')[0]
        val=i.split('=')[1]
        playlist[key]=val
    return playlist
    
def convert_dict_to_token(playlist):
    token = "&".join(["=".join([key, str(val)]) for key, val in playlist.items()])
    return token

def get_next_url_and_token(current_token, skip):
    should_end_session = True
    speech_output = ''
    playlist = convert_token_to_dict(current_token)
    next_url = None
    title = None
    shuffle_mode = int(playlist['s'])
    loop_mode = int(playlist['l'])
    next_playing = int(playlist['p'])
    autoplay = int(playlist['a'])
    if not autoplay and skip != 0:
        return None, convert_dict_to_token(playlist), None
    number_of_videos = sum('v' in i for i in playlist.keys())
    if shuffle_mode and skip != 0:
        for i in range(int(next_playing), number_of_videos-1):
            playlist['v'+str(i)] = playlist['v'+str(i+1)]
        del(playlist['v'+str(number_of_videos-1)])
        number_of_videos = sum('v' in i for i in playlist.keys())
        if number_of_videos == 0:
            return None, convert_dict_to_token(playlist), None
    while next_url is None:
        next_playing = next_playing + skip
        if shuffle_mode and skip != 0:
            next_playing = randint(0,number_of_videos-1)
        if next_playing < 0:
            if loop_mode:
                next_playing = number_of_videos - 1
            else:
                next_playing = 0
        if next_playing >= number_of_videos and loop_mode:
            next_playing = 0
        next_key = 'v'+str(next_playing)
        if next_key not in playlist:
            break
        next_id = playlist[next_key]
        next_url, title = get_url_and_title(next_id)
        if skip == 0:
            break
    playlist['p'] = str(next_playing)
    next_token = convert_dict_to_token(playlist)
    return next_url, next_token, title

def get_time_zone(event):
    try:
        deviceId = event['context']['System']['device']['deviceId']
        apiAccessToken = event['context']['System']['apiAccessToken']
        apiEndpoint = event['context']['System']['apiEndpoint']
        headers = {'Authorization': 'Bearer '+apiAccessToken}
        url = apiEndpoint + '/v2/devices/'+deviceId+'/settings/System.timeZone'
        r = requests.get(url, headers=headers)
        return r.json()
    except:
        return []

def stopped(event):
    offsetInMilliseconds = event['request']['offsetInMilliseconds']
    logger.info("Stopped at %s" % offsetInMilliseconds)

def started(event):
    logger.info("Started")
    logger.info(event)
    current_token = event['context']['AudioPlayer']['token']
    playlist = convert_token_to_dict(current_token)
    now_playing = playlist['p']
    id = playlist['v'+now_playing]
    next_url, title = get_url_and_title(id)
    if title:
        add_to_list(event, title)

def finished(event):
    logger.info('finished')
    token = event['request']['token']

def failed(event):
    logger.info("Playback failed")
    logger.info(event)
    if 'error' in event['request']:
        logger.info(event['request']['error'])
    should_end_session = True
    playBehavior = 'REPLACE_ALL'
    current_token = event['request']['token']
    skip = 1
    next_url, next_token, title = get_next_url_and_token(current_token, skip)
    if title is None:
        return do_nothing()
    return build_response(build_audio_enqueue_response(should_end_session, next_url, current_token, next_token, playBehavior))

def skill_expired():
    speech_output='<speak><voice name="Brian"><prosody rate="medium">'
    speech_output += 'Hi there, this is the developer. Unfortunately your patreon subscription has expired. '
    speech_output += 'If you would like to continue using this skill, please go to patreon.com/alexayoutube to renew your subscription. '
    speech_output += '</prosody></voice></speak> '
    return build_response(build_cardless_speechlet_response(speech_output, '', True, 'SSML'))