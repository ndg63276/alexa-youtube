# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import try_get


class ThisOldHouseIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisoldhouse\.com/(?:watch|how-to|tv-episode)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.thisoldhouse.com/how-to/how-to-build-storage-bench',
        'md5': '568acf9ca25a639f0c4ff905826b662f',
        'info_dict': {
            'id': '2REGtUDQ',
            'ext': 'mp4',
            'title': 'How to Build a Storage Bench',
            'description': 'In the workshop, Tom Silva and Kevin O\'Connor build a storage bench for an entryway.',
            'timestamp': 1442548800,
            'upload_date': '20150918',
        }
    }, {
        'url': 'https://www.thisoldhouse.com/watch/arlington-arts-crafts-arts-and-crafts-class-begins',
        'only_matching': True,
    }, {
        'url': 'https://www.thisoldhouse.com/tv-episode/ask-toh-shelf-rough-electric',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            (r'data-mid=(["\'])(?P<id>(?:(?!\1).)+)\1',
             r'id=(["\'])inline-video-player-(?P<id>(?:(?!\1).)+)\1'),
            webpage, 'video id', default=None, group='id')
        if not video_id:
            drupal_settings = self._parse_json(self._search_regex(
                r'jQuery\.extend\(Drupal\.settings\s*,\s*({.+?})\);',
                webpage, 'drupal settings'), display_id)
            video_id = try_get(
                drupal_settings, lambda x: x['jwplatform']['video_id'],
                compat_str) or list(drupal_settings['comScore'])[0]
        return self.url_result('jwplatform:' + video_id, 'JWPlatform', video_id)
