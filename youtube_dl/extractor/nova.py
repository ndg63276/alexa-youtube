# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    js_to_json,
    qualities,
    unified_strdate,
    url_or_none,
)


class NovaEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://media\.cms\.nova\.cz/embed/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://media.cms.nova.cz/embed/8o0n0r?autoplay=1',
        'md5': 'b3834f6de5401baabf31ed57456463f7',
        'info_dict': {
            'id': '8o0n0r',
            'ext': 'mp4',
            'title': '2180. díl',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 2578,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        bitrates = self._parse_json(
            self._search_regex(
                r'(?s)(?:src|bitrates)\s*=\s*({.+?})\s*;', webpage, 'formats'),
            video_id, transform_source=js_to_json)

        QUALITIES = ('lq', 'mq', 'hq', 'hd')
        quality_key = qualities(QUALITIES)

        formats = []
        for format_id, format_list in bitrates.items():
            if not isinstance(format_list, list):
                continue
            for format_url in format_list:
                format_url = url_or_none(format_url)
                if not format_url:
                    continue
                f = {
                    'url': format_url,
                }
                f_id = format_id
                for quality in QUALITIES:
                    if '%s.mp4' % quality in format_url:
                        f_id += '-%s' % quality
                        f.update({
                            'quality': quality_key(quality),
                            'format_note': quality.upper(),
                        })
                        break
                f['format_id'] = f_id
                formats.append(f)
        self._sort_formats(formats)

        title = self._og_search_title(
            webpage, default=None) or self._search_regex(
            (r'<value>(?P<title>[^<]+)',
             r'videoTitle\s*:\s*(["\'])(?P<value>(?:(?!\1).)+)\1'), webpage,
            'title', group='value')
        thumbnail = self._og_search_thumbnail(
            webpage, default=None) or self._search_regex(
            r'poster\s*:\s*(["\'])(?P<value>(?:(?!\1).)+)\1', webpage,
            'thumbnail', fatal=False, group='value')
        duration = int_or_none(self._search_regex(
            r'videoDuration\s*:\s*(\d+)', webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }


class NovaIE(InfoExtractor):
    IE_DESC = 'TN.cz, Prásk.tv, Nova.cz, Novaplus.cz, FANDA.tv, Krásná.cz and Doma.cz'
    _VALID_URL = r'https?://(?:[^.]+\.)?(?P<site>tv(?:noviny)?|tn|novaplus|vymena|fanda|krasna|doma|prask)\.nova\.cz/(?:[^/]+/)+(?P<id>[^/]+?)(?:\.html|/|$)'
    _TESTS = [{
        'url': 'http://tn.nova.cz/clanek/tajemstvi-ukryte-v-podzemi-specialni-nemocnice-v-prazske-krci.html#player_13260',
        'md5': '1dd7b9d5ea27bc361f110cd855a19bd3',
        'info_dict': {
            'id': '1757139',
            'display_id': 'tajemstvi-ukryte-v-podzemi-specialni-nemocnice-v-prazske-krci',
            'ext': 'mp4',
            'title': 'Podzemní nemocnice v pražské Krči',
            'description': 'md5:f0a42dd239c26f61c28f19e62d20ef53',
            'thumbnail': r're:^https?://.*\.(?:jpg)',
        }
    }, {
        'url': 'http://fanda.nova.cz/clanek/fun-and-games/krvavy-epos-zaklinac-3-divoky-hon-vychazi-vyhrajte-ho-pro-sebe.html',
        'info_dict': {
            'id': '1753621',
            'ext': 'mp4',
            'title': 'Zaklínač 3: Divoký hon',
            'description': 're:.*Pokud se stejně jako my nemůžete.*',
            'thumbnail': r're:https?://.*\.jpg(\?.*)?',
            'upload_date': '20150521',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        # media.cms.nova.cz embed
        'url': 'https://novaplus.nova.cz/porad/ulice/epizoda/18760-2180-dil',
        'info_dict': {
            'id': '8o0n0r',
            'ext': 'mp4',
            'title': '2180. díl',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 2578,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': [NovaEmbedIE.ie_key()],
    }, {
        'url': 'http://sport.tn.nova.cz/clanek/sport/hokej/nhl/zivot-jde-dal-hodnotil-po-vyrazeni-z-playoff-jiri-sekac.html',
        'only_matching': True,
    }, {
        'url': 'http://fanda.nova.cz/clanek/fun-and-games/krvavy-epos-zaklinac-3-divoky-hon-vychazi-vyhrajte-ho-pro-sebe.html',
        'only_matching': True,
    }, {
        'url': 'http://doma.nova.cz/clanek/zdravi/prijdte-se-zapsat-do-registru-kostni-drene-jiz-ve-stredu-3-cervna.html',
        'only_matching': True,
    }, {
        'url': 'http://prask.nova.cz/clanek/novinky/co-si-na-sobe-nase-hvezdy-nechaly-pojistit.html',
        'only_matching': True,
    }, {
        'url': 'http://tv.nova.cz/clanek/novinky/zivot-je-zivot-bondovsky-trailer.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')
        site = mobj.group('site')

        webpage = self._download_webpage(url, display_id)

        # novaplus
        embed_id = self._search_regex(
            r'<iframe[^>]+\bsrc=["\'](?:https?:)?//media\.cms\.nova\.cz/embed/([^/?#&]+)',
            webpage, 'embed url', default=None)
        if embed_id:
            return self.url_result(
                'https://media.cms.nova.cz/embed/%s' % embed_id,
                ie=NovaEmbedIE.ie_key(), video_id=embed_id)

        video_id = self._search_regex(
            [r"(?:media|video_id)\s*:\s*'(\d+)'",
             r'media=(\d+)',
             r'id="article_video_(\d+)"',
             r'id="player_(\d+)"'],
            webpage, 'video id')

        config_url = self._search_regex(
            r'src="(https?://(?:tn|api)\.nova\.cz/bin/player/videojs/config\.php\?[^"]+)"',
            webpage, 'config url', default=None)
        config_params = {}

        if not config_url:
            player = self._parse_json(
                self._search_regex(
                    r'(?s)Player\s*\(.+?\s*,\s*({.+?\bmedia\b["\']?\s*:\s*["\']?\d+.+?})\s*\)', webpage,
                    'player', default='{}'),
                video_id, transform_source=js_to_json, fatal=False)
            if player:
                config_url = url_or_none(player.get('configUrl'))
                params = player.get('configParams')
                if isinstance(params, dict):
                    config_params = params

        if not config_url:
            DEFAULT_SITE_ID = '23000'
            SITES = {
                'tvnoviny': DEFAULT_SITE_ID,
                'novaplus': DEFAULT_SITE_ID,
                'vymena': DEFAULT_SITE_ID,
                'krasna': DEFAULT_SITE_ID,
                'fanda': '30',
                'tn': '30',
                'doma': '30',
            }

            site_id = self._search_regex(
                r'site=(\d+)', webpage, 'site id', default=None) or SITES.get(
                site, DEFAULT_SITE_ID)

            config_url = 'https://api.nova.cz/bin/player/videojs/config.php'
            config_params = {
                'site': site_id,
                'media': video_id,
                'quality': 3,
                'version': 1,
            }

        config = self._download_json(
            config_url, display_id,
            'Downloading config JSON', query=config_params,
            transform_source=lambda s: s[s.index('{'):s.rindex('}') + 1])

        mediafile = config['mediafile']
        video_url = mediafile['src']

        m = re.search(r'^(?P<url>rtmpe?://[^/]+/(?P<app>[^/]+?))/&*(?P<playpath>.+)$', video_url)
        if m:
            formats = [{
                'url': m.group('url'),
                'app': m.group('app'),
                'play_path': m.group('playpath'),
                'player_path': 'http://tvnoviny.nova.cz/static/shared/app/videojs/video-js.swf',
                'ext': 'flv',
            }]
        else:
            formats = [{
                'url': video_url,
            }]
        self._sort_formats(formats)

        title = mediafile.get('meta', {}).get('title') or self._og_search_title(webpage)
        description = clean_html(self._og_search_description(webpage, default=None))
        thumbnail = config.get('poster')

        if site == 'novaplus':
            upload_date = unified_strdate(self._search_regex(
                r'(\d{1,2}-\d{1,2}-\d{4})$', display_id, 'upload date', default=None))
        elif site == 'fanda':
            upload_date = unified_strdate(self._search_regex(
                r'<span class="date_time">(\d{1,2}\.\d{1,2}\.\d{4})', webpage, 'upload date', default=None))
        else:
            upload_date = None

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'thumbnail': thumbnail,
            'formats': formats,
        }
