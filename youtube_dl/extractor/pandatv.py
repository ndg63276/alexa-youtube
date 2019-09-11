# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    qualities,
)


class PandaTVIE(InfoExtractor):
    IE_DESC = '熊猫TV'
    _VALID_URL = r'https?://(?:www\.)?panda\.tv/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.panda.tv/66666',
        'info_dict': {
            'id': '66666',
            'title': 're:.+',
            'uploader': '刘杀鸡',
            'ext': 'flv',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Live stream is offline',
    }, {
        'url': 'https://www.panda.tv/66666',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        config = self._download_json(
            'https://www.panda.tv/api_room_v2?roomid=%s' % video_id, video_id)

        error_code = config.get('errno', 0)
        if error_code != 0:
            raise ExtractorError(
                '%s returned error %s: %s'
                % (self.IE_NAME, error_code, config['errmsg']),
                expected=True)

        data = config['data']
        video_info = data['videoinfo']

        # 2 = live, 3 = offline
        if video_info.get('status') != '2':
            raise ExtractorError(
                'Live stream is offline', expected=True)

        title = data['roominfo']['name']
        uploader = data.get('hostinfo', {}).get('name')
        room_key = video_info['room_key']
        stream_addr = video_info.get(
            'stream_addr', {'OD': '1', 'HD': '1', 'SD': '1'})

        # Reverse engineered from web player swf
        # (http://s6.pdim.gs/static/07153e425f581151.swf at the moment of
        # writing).
        plflag0, plflag1 = video_info['plflag'].split('_')
        plflag0 = int(plflag0) - 1
        if plflag1 == '21':
            plflag0 = 10
            plflag1 = '4'
        live_panda = 'live_panda' if plflag0 < 1 else ''

        plflag_auth = self._parse_json(video_info['plflag_list'], video_id)
        sign = plflag_auth['auth']['sign']
        ts = plflag_auth['auth']['time']
        rid = plflag_auth['auth']['rid']

        quality_key = qualities(['OD', 'HD', 'SD'])
        suffix = ['_small', '_mid', '']
        formats = []
        for k, v in stream_addr.items():
            if v != '1':
                continue
            quality = quality_key(k)
            if quality <= 0:
                continue
            for pref, (ext, pl) in enumerate((('m3u8', '-hls'), ('flv', ''))):
                formats.append({
                    'url': 'https://pl%s%s.live.panda.tv/live_panda/%s%s%s.%s?sign=%s&ts=%s&rid=%s'
                    % (pl, plflag1, room_key, live_panda, suffix[quality], ext, sign, ts, rid),
                    'format_id': '%s-%s' % (k, ext),
                    'quality': quality,
                    'source_preference': pref,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._live_title(title),
            'uploader': uploader,
            'formats': formats,
            'is_live': True,
        }
