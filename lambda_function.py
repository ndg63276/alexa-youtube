# -*- coding: utf-8 -*-
from __future__ import print_function
from os import environ
from googleapiclient.discovery import build
from pytube import YouTube
import logging
from random import shuffle, randint
from botocore.vendored import requests
import urllib
from time import time
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
DEVELOPER_KEY=environ['DEVELOPER_KEY']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

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
'nothingplaying':"Nothing is currently playing.",
'sorryskipby':"Sorry, I didn't hear how much to skip by",
'sorryskipto':"Sorry, I didn't hear where to skip to",
'ok':"OK",
'currentposition':"The current position is",
'hours':"hours",
'hour':"hour",
'minutes':"minutes",
'minute':"minute",
'seconds':"seconds",
'second':"second",
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
'nothingplaying':"Il n'y a aucune lecture en cours.",
'sorryskipby':"Désolé, je n'ai pas compris de combien je devais avancer ou reculer.",
'sorryskipto':"Désolé, je n'ai pas compris de combien je devais avancer ou reculer.",
'ok':"OK"
}
strings_it = {
'welcome1':"Benvenuto su YouTube. Dì, per esempio, riproduci video dei Beatles.",
'welcome2':"Oppure puoi dire, canzoni casuali di Michael Jackson.",
'help':"Per esempio dì, riproduci i video dei Fall out Boy",
'illegal':"Non puoi fare questo con questa skill.",
'gonewrong':"Spiacente, qualcosa è andato storto",
'playlist':"La playlist",
'channel':"Il canale",
'video':"Il video",
'notworked':"non ha funzionato, dovrei provare la prossima?",
'playing':"Riproduco",
'pausing':"Ciao da Youtube",
'nomoreitems':"Non ci sono più elementi nella playlist.",
'resuming':"Riprendo",
'noresume':"Non ero in grado di riprendere il video.",
'novideo':"Non ero in grado di riprodurre un video",
'notitle':"Non riesco a trovare il nome del video corrente.",
'nowplaying':"Ora riproduco",
'nothingplaying':"Al momento non sto riproducendo nulla.",
'sorryskipby':"Spiacente, non ho capito di quanto saltare",
'sorryskipto':"Spiacente, non ho capito dove saltare",
'ok':"OK"
}
strings_de = {
'welcome1':"Willkommen bei Youtube. Sagen Sie zum Beispiel, spiel Videos von The Beatles.",
'welcome2':"Oder Sie können sagen, misch Songs von Michael Jackson.",
'help':"Sie können sagen zum Beispiel, spiel Videos von Fall Out Boy ab.",
'illegal':"Sie können dies mit dieses Skill nicht tun.",
'gonewrong':"Es tut mir Leid, etwas ist schief gelaufen",
'playlist':"Die Wiedergabeliste",
'channel':"Der Kanal",
'video':"Das Video",
'notworked':"hat nicht funktioniert, soll ich das nächste versuchen?",
'playing':"Spielen",
'pausing':"Pausieren",
'nomoreitems':"Die Wiedergabeliste enthält keine weiteren Elemente.",
'resuming':"Fortfahren",
'noresume':"Ich konnte nicht weiter spielen.",
'novideo':"Ich konnte dieses Video nicht abspielen.",
'notitle':"Ich kann den Namen des aktuellen Videos nicht herausfinden.",
'nowplaying':"Jetzt spielt",
'nothingplaying':"Es wird momentan nichts abgespielt.",
'sorryskipby':"Entschuldigung, ich habe nicht gehört, wie viel ich überspringen soll",
'sorryskipto':"Entschuldigung, ich habe nicht gehört, wo ich überspringen soll",
'ok':"OK"
}
strings_es = {
'welcome1':"Bienvenido a Youtube. Di, por ejemplo, pon videos de los Beatles.",
'welcome2':"O puedes decir, aleatorio canciones de Michael Jackson.",
'help':"por ejemplo di, pon videos de Fall Out Boy",
'illegal':"Tu no puedes hacer esto con esta skill .",
'gonewrong':"Lo sentimos, ocurrio un error",
'playlist':"la playlist",
'channel':"el canal",
'video':"el video",
'notworked':"no ha funcionado desea la siguiente?",
'playing':"sonando",
'pausing':"para",
'nomoreitems':"No hay items en la playlist",
'resuming':"resumiendo",
'noresume':"No hay resumen del video",
'novideo':"No se puede reproducir el video",
'notitle':"No puedo encontrar el titulo del video",
'nowplaying':"ahora sonando",
'nothingplaying':"Nada esta sonando",
'sorryskipby':"Lo siento no escuche cuando adelantar",
'sorryskipto':"Lo siento no escuche a donde adelantar",
'ok':"OK"
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
    elif event['request']['locale'][0:2] == 'it':
        strings = strings_it
    elif event['request']['locale'][0:2] == 'de':
        strings = strings_de
    elif event['request']['locale'][0:2] == 'es':
        strings = strings_es
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
    search_intents = ["SearchIntent", "PlayOneIntent", "PlaylistIntent", "MyPlaylistIntent", "ShuffleMyPlaylistIntent", "ChannelIntent", "ShuffleIntent", "ShufflePlaylistIntent", "ShuffleChannelIntent"]
    if intent_name in search_intents:
        return search(intent, session)
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
    channel_id = ''
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
    return search(intent, session)

def search(intent, session):
    startTime = time()
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
    else:
        videos = video_search(query)
        playlist_channel_video = strings['video']
    next_url = None
    for i,id in enumerate(videos):
        if playlist_channel_video != strings['video'] and time() - startTime > 8:
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
    return resume(event, offsetInMilliseconds = current_offsetInMilliseconds + skip_by_offsetInMilliseconds)

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
    return resume(event, offsetInMilliseconds = offsetInMilliseconds)

def resume(event, say_title = False, offsetInMilliseconds = None):
    if 'token' not in event['context']['AudioPlayer']:
        return get_welcome_response()
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
