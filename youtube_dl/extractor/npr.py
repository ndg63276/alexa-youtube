from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    qualities,
)


class NprIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?npr\.org/(?:sections/[^/]+/)?\d{4}/\d{2}/\d{2}/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.npr.org/sections/allsongs/2015/10/21/449974205/new-music-from-beach-house-chairlift-cmj-discoveries-and-more',
        'info_dict': {
            'id': '449974205',
            'title': 'New Music From Beach House, Chairlift, CMJ Discoveries And More'
        },
        'playlist_count': 7,
    }, {
        'url': 'https://www.npr.org/sections/deceptivecadence/2015/10/09/446928052/music-from-the-shadows-ancient-armenian-hymns-and-piano-jazz',
        'info_dict': {
            'id': '446928052',
            'title': "Songs We Love: Tigran Hamasyan, 'Your Mercy is Boundless'"
        },
        'playlist': [{
            'md5': '12fa60cb2d3ed932f53609d4aeceabf1',
            'info_dict': {
                'id': '446929930',
                'ext': 'mp3',
                'title': 'Your Mercy is Boundless (Bazum en Qo gtutyunqd)',
                'duration': 402,
            },
        }],
    }, {
        # mutlimedia, not media title
        'url': 'https://www.npr.org/2017/06/19/533198237/tigers-jaw-tiny-desk-concert',
        'info_dict': {
            'id': '533198237',
            'title': 'Tigers Jaw: Tiny Desk Concert',
        },
        'playlist': [{
            'md5': '12fa60cb2d3ed932f53609d4aeceabf1',
            'info_dict': {
                'id': '533201718',
                'ext': 'mp4',
                'title': 'Tigers Jaw: Tiny Desk Concert',
                'duration': 402,
            },
        }],
        'expected_warnings': ['Failed to download m3u8 information'],
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        story = self._download_json(
            'http://api.npr.org/query', playlist_id, query={
                'id': playlist_id,
                'fields': 'audio,multimedia,title',
                'format': 'json',
                'apiKey': 'MDAzMzQ2MjAyMDEyMzk4MTU1MDg3ZmM3MQ010',
            })['list']['story'][0]
        playlist_title = story.get('title', {}).get('$text')

        KNOWN_FORMATS = ('threegp', 'm3u8', 'smil', 'mp4', 'mp3')
        quality = qualities(KNOWN_FORMATS)

        entries = []
        for media in story.get('audio', []) + story.get('multimedia', []):
            media_id = media['id']

            formats = []
            for format_id, formats_entry in media.get('format', {}).items():
                if not formats_entry:
                    continue
                if isinstance(formats_entry, list):
                    formats_entry = formats_entry[0]
                format_url = formats_entry.get('$text')
                if not format_url:
                    continue
                if format_id in KNOWN_FORMATS:
                    if format_id == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            format_url, media_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls', fatal=False))
                    elif format_id == 'smil':
                        smil_formats = self._extract_smil_formats(
                            format_url, media_id, transform_source=lambda s: s.replace(
                                'rtmp://flash.npr.org/ondemand/', 'https://ondemand.npr.org/'))
                        self._check_formats(smil_formats, media_id)
                        formats.extend(smil_formats)
                    else:
                        formats.append({
                            'url': format_url,
                            'format_id': format_id,
                            'quality': quality(format_id),
                        })
            self._sort_formats(formats)

            entries.append({
                'id': media_id,
                'title': media.get('title', {}).get('$text') or playlist_title,
                'thumbnail': media.get('altImageUrl', {}).get('$text'),
                'duration': int_or_none(media.get('duration', {}).get('$text')),
                'formats': formats,
            })

        return self.playlist_result(entries, playlist_id, playlist_title)
