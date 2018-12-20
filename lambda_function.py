# -*- coding: utf-8 -*-
from __future__ import print_function
from os import environ
from googleapiclient.discovery import build
from pytube import YouTube
import logging
from random import shuffle, randint
from botocore.vendored import requests
import json
import urllib
from time import time
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
DEVELOPER_KEY=environ['DEVELOPER_KEY']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

strings_en = {
'welcome1':"Welcome to Youtube. Say, for example, play videos by The Beatles.",
'welcome2':"Or you can say, shuffle songs by Michael Jackson.",
'help':"For example say, play videos by Fall Out Boy",
'illegal':"You can't do that with this skill.",
'gonewrong':"Sorry, something's gone wrong",
'playlist':"The playlist",
'channel':"The channel",
'video':"The video",
'notworked':"hasn't worked, shall I try the next one?",
'playing':"Playing",
'pausing':"Pausing",
'nomoreitems':"There are no more items in the playlist.",
'resuming':"Resuming",
'noresume':"I wasn't able to resume playing.",
'novideo':"I wasn't able to play a video.",
'notitle':"I can't find out the name of the current video.",
'nowplaying':"Now playing",
'nothingplaying':"Nothing is currently playing."
}
strings_fr = {
'welcome1':"Bienvenue sur Youtube. Dite, par exemple, jouer une vidéo de Madonna.",
'welcome2':"Ou vous pouvez dire, chanson aléatoire de Michael Jackson.",
'help':"Par exemple dite, joue une vidéo de Michael Jackson",
'illegal':"Vous ne pouvez pas faire ça avec cette skill.",
'gonewrong':"Désolé, quelque chose n'a pas fonctionné",
'playlist':"La playlist",
'channel':"La chaîne",
'video':"The vidéo",
'notworked':"ne fonctionne pas, dois je essayer la suivante ?",
'playing':"Lecture de",
'pausing':"En pause",
'nomoreitems':"Il n'y a plus rien à lire dans cette playlist.",
'resuming':"Reprise",
'noresume':"Je n'ai pas pu reprendre la lecture.",
'novideo':"Je ne peux pas lire la vidéo.",
'notitle':"Je ne retrouve pas le nom de cette vidéo.",
'nowplaying':"Vous écoutez ",
'nothingplaying':"Il n'y a aucune lecture en cours."
}

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


def build_cardless_speechlet_response(output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

 
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


# --------------- Main handler ------------------

def lambda_handler(event, context):
    global strings
    if event['request']['locale'][0:2] == 'fr':
        strings = strings_fr
    else:
        strings = strings_en
    if event['request']['type'] == "LaunchRequest":
        return get_welcome_response()
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event)
    elif event['request']['type'] == "SessionEndedRequest":
        logger.info("on_session_ended")
    elif event['request']['type'].startswith('AudioPlayer'):
        return handle_playback(event)
        
# --------------- Events ------------------

def on_intent(event):
    intent_request = event['request']
    session = event['session']
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    # Dispatch to your skill's intent handlers
    if intent_name == "SearchIntent":
        return search(intent, session)
    elif intent_name == "PlaylistIntent":
        return search(intent, session)
    elif intent_name == "ChannelIntent":
        return search(intent, session)
    elif intent_name == "ShuffleIntent":
        return search(intent, session)
    elif intent_name == "ShufflePlaylistIntent":
        return search(intent, session)
    elif intent_name == "ShuffleChannelIntent":
        return search(intent, session)
    elif intent_name == "AMAZON.YesIntent":
        return yes_intent(session)
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
        return stop(intent, session)
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

def get_welcome_response():
    speech_output = strings['welcome1']
    reprompt_text = strings['welcome2']
    should_end_session = False
    return build_response(build_cardless_speechlet_response(speech_output, reprompt_text, should_end_session))
        
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

def video_search(query):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=50,
        type='video'
        ).execute()
    videos = []
    for search_result in search_response.get('items', []):
        if 'videoId' in search_result['id']:
            videos.append(search_result['id']['videoId'])
    return videos

def playlist_search(query, sr):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=10,
        type='playlist'
        ).execute()
    playlist_id = search_response.get('items')[sr]['id']['playlistId']
    logger.info('Playlist info: https://www.youtube.com/playlist?list='+playlist_id)
    playlist_title = search_response.get('items')[sr]['snippet']['title']
    videos = []
    data={'nextPageToken':''}
    while 'nextPageToken' in data and len(videos) < 25:
        next_page_token = data['nextPageToken']
        data = json.loads(requests.get('https://www.googleapis.com/youtube/v3/playlistItems?pageToken={}&part=snippet&playlistId={}&key={}'.format(next_page_token,playlist_id,DEVELOPER_KEY)).text)
        for item in data['items']:
            try:
                videos.append(item['snippet']['resourceId']['videoId'])
            except:
                pass
    return videos, playlist_title

def channel_search(query, sr):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
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
    while 'nextPageToken' in data and len(videos) < 25:
        next_page_token = data['nextPageToken']
        data = json.loads(requests.get('https://www.googleapis.com/youtube/v3/search?pageToken={}&part=snippet&channelId={}&key={}'.format(next_page_token,playlist_id,DEVELOPER_KEY)).text)
        for item in data['items']:
            try:
                videos.append(item['id']['videoId'])
            except:
                pass
    return videos, playlist_title

def get_url_and_title(id):
    logger.info('Getting url for https://www.youtube.com/watch?v='+id)
    try:
        yt=YouTube('https://www.youtube.com/watch?v='+id)
        first_stream = yt.streams.filter(only_audio=True, subtype='mp4').first()
        logger.info(first_stream.url)
        return first_stream.url, yt.title
    except:
        logger.info('Unable to get URL for '+id)
        return get_live_video_url_and_title(id)

def get_live_video_url_and_title(id):
    logger.info('Live video?')
    info_url = 'https://www.youtube.com/get_video_info?&video_id='+id
    r = requests.get(info_url)
    info = convert_token_to_dict(r.text)
    try:
        raw_url = info['hlsvp']
        url = urllib.unquote(raw_url)
        return url, 'live video'
    except:
        logger.info('Unable to get hlsvp')
        return None, None

def yes_intent(session):
    sessionAttributes = session.get('attributes')
    if not sessionAttributes or 'intent' not in sessionAttributes or 'sr' not in sessionAttributes:
        return build_response(build_cardless_speechlet_response(strings['gonewrong'], None, True))
    intent = sessionAttributes['intent']
    session['attributes']['sr'] = sessionAttributes['sr'] + 1
    return search(intent, session)

def search(intent, session):
    startTime = time()
    query = intent['slots']['query']['value']
    should_end_session = True
    logger.info('Looking for: ' + query)
    intent_name = intent['name']
    playlist_title = None
    sessionAttributes = session.get('attributes')
    if not sessionAttributes:
        sessionAttributes={'sr':0, 'intent':intent}
    sr = sessionAttributes['sr']
    if intent_name == "PlaylistIntent" or intent_name == "ShufflePlaylistIntent":
        videos, playlist_title = playlist_search(query, sr)
        playlist_channel_video = strings['playlist']
    elif intent_name == "ChannelIntent" or intent_name == "ShuffleChannelIntent":
        videos, playlist_title = channel_search(query, sr)
        playlist_channel_video = strings['channel']
    else:
        videos = video_search(query)
        playlist_channel_video = strings['video']
    next_url = None
    playlist = {}
    playlist['s'] = '0'
    if intent_name == "ShuffleIntent" or intent_name == "ShufflePlaylistIntent" or intent_name == "ShuffleChannelIntent":
        shuffle(videos)
        playlist['s'] = '1'
    playlist['l'] = '0'
    for i,id in enumerate(videos):
        if playlist_channel_video != 'video' and time() - startTime > 8:
            return build_response(build_cardless_speechlet_response(playlist_channel_video+" "+playlist_title+" " + strings['notworked'], None, False), sessionAttributes)
        playlist['v'+str(i)]=id
        if next_url is None:
            playlist['p'] = i
            next_url, title = get_url_and_title(id)
    next_token = convert_dict_to_token(playlist)
    if playlist_title is None:
        speech_output = strings['playing'] + ' ' + title
    else:
        speech_output = strings['playing'] + ' ' + playlist_title
    card_title = "Youtube"
    return build_response(build_audio_speechlet_response(card_title, speech_output, should_end_session, next_url, next_token))

def stop(intent, session):
    should_end_session = True
    speech_output = strings['pausing']
    return build_response(build_stop_speechlet_response(speech_output, should_end_session))

def nearly_finished(event):
    should_end_session = True
    current_token = event['request']['token']
    skip = 1
    next_url, next_token, title = get_next_url_and_token(current_token, skip)
    if title is None:
        return do_nothing()
    return build_response(build_audio_enqueue_response(should_end_session, next_url, current_token, next_token))

def skip_action(event, skip):
    logger.info("event:")
    logger.info(event)
    logger.info("context:")
    logger.info(event['context'])
    should_end_session = True
    current_token = event['context']['AudioPlayer']['token']
    next_url, next_token, title = get_next_url_and_token(current_token, skip)
    if title is None:
        speech_output = strings['nomoreitems']
        return build_response(build_short_speechlet_response(speech_output, should_end_session))
    speech_output = strings['playing']+' '+title
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, next_token))

def resume(event, say_title = False):
    if 'token' not in event['context']['AudioPlayer']:
        return get_welcome_response()
    current_token = event['context']['AudioPlayer']['token']
    should_end_session = True
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
    speech_output = "OK"
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
    number_of_videos = sum('v' in i for i in playlist.keys())
    while next_url is None:
        next_playing = next_playing + skip
        if shuffle_mode and skip != 0:
            next_playing = randint(1,number_of_videos)
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

def stopped(event):
    offsetInMilliseconds = event['request']['offsetInMilliseconds']
    logger.info("Stopped at %s" % offsetInMilliseconds)

def started(event):
    logger.info("Started")
    token = event['request']['token']

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
