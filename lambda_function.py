from __future__ import print_function
from os import environ
from googleapiclient.discovery import build
from pytube import YouTube
import logging
from random import shuffle, randint
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
DEVELOPER_KEY=environ['DEVELOPER_KEY']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

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


def build_audio_enqueue_response(should_end_session, url, previous_token, next_token):
    return {
        'directives': [{
            'type': 'AudioPlayer.Play',
            'playBehavior': 'ENQUEUE',
            'audioItem': {
                'stream': {
                    'token': str(next_token),
                    'expectedPreviousToken': str(previous_token),
                    'url': url,
                    'offsetInMilliseconds': 0
                }
            }
        }],
        'shouldEndSession': should_end_session
    }


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


def build_response(speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': {},
        'response': speechlet_response
    }


# --------------- Main handler ------------------

def lambda_handler(event, context):
    print(event)
    if event['request']['type'] == "LaunchRequest":
        return get_welcome_response()
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event)
    elif event['request']['type'] == "SessionEndedRequest":
        print("on_session_ended")
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
    elif intent_name == "ShuffleIntent":
        return search(intent, session, shuffle_mode=True)
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
    elif intent_name == "AMAZON.RepeatIntent":
        return illegal_action()
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
        return failed()

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    speech_output = 'Welcome to Youtube. What should I search for?'
    reprompt_text = 'For example say, play videos by Fall Out Boy.'
    should_end_session = False
    return build_response(build_cardless_speechlet_response(speech_output, reprompt_text, should_end_session))
        
def get_help():
    speech_output = 'For example say, play videos by Fall Out Boy'
    card_title = 'Youtube Help'
    should_end_session = False
    return build_response(build_speechlet_response(card_title, speech_output, None, should_end_session))
            
def illegal_action():
    speech_output = 'You can\'t do that with this skill.'
    should_end_session = True
    return build_response(build_short_speechlet_response(speech_output, should_end_session))
        
def do_nothing():
    return build_response({})

def youtube_search(query):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=25,
        type='video'
        ).execute()
    videos = []
    for search_result in search_response.get('items', []):
        videos.append(search_result['id']['videoId'])
    return videos

def get_url_and_title(id):
    print('Getting url for https://www.youtube.com/watch?v='+id)
    try:
        yt=YouTube('https://www.youtube.com/watch?v='+id)
        first_stream = yt.streams.filter(only_audio=True, subtype='mp4').first()
        print(first_stream.url)
        return first_stream.url, yt.title
    except:
        print('Unable to get URL for '+id)
        return None, None

def search(intent, session, shuffle_mode=False):
    query = intent['slots']['query']['value']
    should_end_session = True
    print('Looking for: ' + query)
    videos = youtube_search(query)
    if shuffle_mode:
        shuffle(videos)
    next_url = None
    playlist = {}
    playlist['s'] = '1' if shuffle_mode else '0'
    playlist['l'] = '0'
    for i,id in enumerate(videos):
        playlist['v'+str(i)]=id
        if next_url is None:
            playlist['p'] = i
            next_url, title = get_url_and_title(id)
    next_token = "&".join(["=".join([key, str(val)]) for key, val in playlist.items()])
    speech_output = "Playing " + title
    card_title = "Youtube"
    return build_response(build_audio_speechlet_response(card_title, speech_output, should_end_session, next_url, next_token))

def stop(intent, session):
    should_end_session = True
    speech_output = "Pausing"
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
    print("event:")
    print(event)
    print("context:")
    print(event['context'])
    should_end_session = True
    current_token = event['context']['AudioPlayer']['token']
    next_url, next_token, title = get_next_url_and_token(current_token, skip)
    if title is None:
        speech_output = "There are no more items in the playlist."
        return build_response(build_short_speechlet_response(speech_output, should_end_session))
    speech_output = 'Playing '+title
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, next_token))

def resume(event, say_title = False):
    current_token = event['context']['AudioPlayer']['token']
    should_end_session = True
    speech_output = "Resuming..."
    offsetInMilliseconds = event['context']['AudioPlayer']['offsetInMilliseconds']
    next_url, next_token, title = get_next_url_and_token(current_token, 0)
    if title is None:
        speech_output = "I wasn't able to resume playing."
        return build_response(build_short_speechlet_response(speech_output, should_end_session))
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, current_token, offsetInMilliseconds))

def change_mode(event, mode, value):
    current_token = event['context']['AudioPlayer']['token']
    should_end_session = True
    playlist = convert_token_to_playlist(current_token)
    playlist[mode] = str(value)
    current_token = convert_playlist_to_token(playlist)
    speech_output = "OK"
    offsetInMilliseconds = event['context']['AudioPlayer']['offsetInMilliseconds']
    next_url, next_token, title = get_next_url_and_token(current_token, 0)
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, current_token, offsetInMilliseconds))

def start_over(event):
    current_token = event['context']['AudioPlayer']['token']
    should_end_session = True
    next_url, next_token, title = get_next_url_and_token(current_token, 0)
    if title is None:
        speech_output = "I wasn't able to play a video."
        return build_response(build_short_speechlet_response(speech_output, should_end_session))
    speech_output = "Playing " + title    
    return build_response(build_cardless_audio_speechlet_response(speech_output, should_end_session, next_url, next_token))

def convert_token_to_playlist(token):
    pi=token.split('&')
    playlist={}
    for i in pi:
        key=i.split('=')[0]
        val=i.split('=')[1]
        playlist[key]=val
    return playlist
    
def convert_playlist_to_token(playlist):
    token = "&".join(["=".join([key, str(val)]) for key, val in playlist.items()])
    return token

def get_next_url_and_token(current_token, skip):
    should_end_session = True
    speech_output = ''
    playlist = convert_token_to_playlist(current_token)
    next_url = None
    title = None
    shuffle_mode = int(playlist['s'])
    next_playing = int(playlist['p'])
    number_of_videos = sum('v' in i for i in playlist.keys())
    while next_url is None:
        next_playing = next_playing + skip
        if shuffle_mode and skip != 0:
            next_playing = randint(1,number_of_videos)
        if next_playing < 0:
            next_playing = 0
        next_key = 'v'+str(next_playing)
        if next_key not in playlist:
            break
        next_id = playlist[next_key]
        next_url, title = get_url_and_title(next_id)
        if skip == 0:
            break
    playlist['p'] = str(next_playing)
    next_token = convert_playlist_to_token(playlist)
    return next_url, next_token, title

def stopped(event):
    offsetInMilliseconds = event['request']['offsetInMilliseconds']
    print("Stopped at %s" % offsetInMilliseconds)

def started(event):
    print("Started")
    token = event['request']['token']

def finished(event):
    print('finished')
    token = event['request']['token']

def failed():
    print("Playback failed")


