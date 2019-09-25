# coding: utf-8

from __future__ import unicode_literals

import os
import re
import sys

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..compat import (
    compat_etree_fromstring,
    compat_str,
    compat_urllib_parse_unquote,
    compat_urlparse,
    compat_xml_parse_error,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    HEADRequest,
    is_html,
    js_to_json,
    KNOWN_EXTENSIONS,
    merge_dicts,
    mimetype2ext,
    orderedSet,
    sanitized_Request,
    smuggle_url,
    unescapeHTML,
    unified_strdate,
    unsmuggle_url,
    UnsupportedError,
    xpath_text,
)
from .commonprotocols import RtmpIE



class GenericIE(InfoExtractor):
    IE_DESC = 'Generic downloader that works on some sites'
    _VALID_URL = r'.*'
    IE_NAME = 'generic'
    _TESTS = [
        # google redirect
        {
            'url': 'http://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&cad=rja&ved=0CCUQtwIwAA&url=http%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DcmQHVoWB5FY&ei=F-sNU-LLCaXk4QT52ICQBQ&usg=AFQjCNEw4hL29zgOohLXvpJ-Bdh2bils1Q&bvm=bv.61965928,d.bGE',
            'info_dict': {
                'id': 'cmQHVoWB5FY',
                'ext': 'mp4',
                'upload_date': '20130224',
                'uploader_id': 'TheVerge',
                'description': r're:^Chris Ziegler takes a look at the\.*',
                'uploader': 'The Verge',
                'title': 'First Firefox OS phones side-by-side',
            },
            'params': {
                'skip_download': False,
            }
        },

        # YouTube embed
        {
            'url': 'http://www.badzine.de/ansicht/datum/2014/06/09/so-funktioniert-die-neue-englische-badminton-liga.html',
            'info_dict': {
                'id': 'FXRb4ykk4S0',
                'ext': 'mp4',
                'title': 'The NBL Auction 2014',
                'uploader': 'BADMINTON England',
                'uploader_id': 'BADMINTONEvents',
                'upload_date': '20140603',
                'description': 'md5:9ef128a69f1e262a700ed83edb163a73',
            },
            'add_ie': ['Youtube'],
            'params': {
                'skip_download': True,
            }
        },

        # YouTube embed via <data-embed-url="">
        {
            'url': 'https://play.google.com/store/apps/details?id=com.gameloft.android.ANMP.GloftA8HM',
            'info_dict': {
                'id': '4vAffPZIT44',
                'ext': 'mp4',
                'title': 'Asphalt 8: Airborne - Update - Welcome to Dubai!',
                'uploader': 'Gameloft',
                'uploader_id': 'gameloft',
                'upload_date': '20140828',
                'description': 'md5:c80da9ed3d83ae6d1876c834de03e1c4',
            },
            'params': {
                'skip_download': True,
            }
        },
        # YouTube <object> embed
        {
            'url': 'http://www.improbable.com/2017/04/03/untrained-modern-youths-and-ancient-masters-in-selfie-portraits/',
            'md5': '516718101ec834f74318df76259fb3cc',
            'info_dict': {
                'id': 'msN87y-iEx0',
                'ext': 'webm',
                'title': 'Feynman: Mirrors FUN TO IMAGINE 6',
                'upload_date': '20080526',
                'description': 'md5:0ffc78ea3f01b2e2c247d5f8d1d3c18d',
                'uploader': 'Christopher Sykes',
                'uploader_id': 'ChristopherJSykes',
            },
            'add_ie': ['Youtube'],
        },
        # Camtasia studio

        {
            'url': 'https://www.youtube.com/shared?ci=1nEzmT-M4fU',
            'info_dict': {
                'id': 'uPDB5I9wfp8',
                'ext': 'webm',
                'title': 'Pocoyo: 90 minutos de episódios completos Português para crianças - PARTE 3',
                'description': 'md5:d9e4d9346a2dfff4c7dc4c8cec0f546d',
                'upload_date': '20160219',
                'uploader': 'Pocoyo - Português (BR)',
                'uploader_id': 'PocoyoBrazil',
            },
            'add_ie': [YoutubeIE.ie_key()],
            'params': {
                'skip_download': True,
            },
        },

    ]

    def report_following_redirect(self, new_url):
        """Report information extraction."""
        self._downloader.to_screen('[redirect] Following redirect to %s' % new_url)

    def _extract_rss(self, url, video_id, doc):
        playlist_title = doc.find('./channel/title').text
        playlist_desc_el = doc.find('./channel/description')
        playlist_desc = None if playlist_desc_el is None else playlist_desc_el.text

        entries = []
        for it in doc.findall('./channel/item'):
            next_url = None
            enclosure_nodes = it.findall('./enclosure')
            for e in enclosure_nodes:
                next_url = e.attrib.get('url')
                if next_url:
                    break

            if not next_url:
                next_url = xpath_text(it, 'link', fatal=False)

            if not next_url:
                continue

            entries.append({
                '_type': 'url_transparent',
                'url': next_url,
                'title': it.find('title').text,
            })

        return {
            '_type': 'playlist',
            'id': url,
            'title': playlist_title,
            'description': playlist_desc,
            'entries': entries,
        }

    def _extract_camtasia(self, url, video_id, webpage):
        """ Returns None if no camtasia video can be found. """

        camtasia_cfg = self._search_regex(
            r'fo\.addVariable\(\s*"csConfigFile",\s*"([^"]+)"\s*\);',
            webpage, 'camtasia configuration file', default=None)
        if camtasia_cfg is None:
            return None

        title = self._html_search_meta('DC.title', webpage, fatal=True)

        camtasia_url = compat_urlparse.urljoin(url, camtasia_cfg)
        camtasia_cfg = self._download_xml(
            camtasia_url, video_id,
            note='Downloading camtasia configuration',
            errnote='Failed to download camtasia configuration')
        fileset_node = camtasia_cfg.find('./playlist/array/fileset')

        entries = []
        for n in fileset_node.getchildren():
            url_n = n.find('./uri')
            if url_n is None:
                continue

            entries.append({
                'id': os.path.splitext(url_n.text.rpartition('/')[2])[0],
                'title': '%s - %s' % (title, n.tag),
                'url': compat_urlparse.urljoin(url, url_n.text),
                'duration': float_or_none(n.find('./duration').text),
            })

        return {
            '_type': 'playlist',
            'entries': entries,
            'title': title,
        }

    def _real_extract(self, url):
        if url.startswith('//'):
            return self.url_result(self.http_scheme() + url)

        parsed_url = compat_urlparse.urlparse(url)
        if not parsed_url.scheme:
            default_search = self._downloader.params.get('default_search')
            if default_search is None:
                default_search = 'fixup_error'

            if default_search in ('auto', 'auto_warning', 'fixup_error'):
                if re.match(r'^[^\s/]+\.[^\s/]+/', url):
                    self._downloader.report_warning('The url doesn\'t specify the protocol, trying with http')
                    return self.url_result('http://' + url)
                elif default_search != 'fixup_error':
                    if default_search == 'auto_warning':
                        if re.match(r'^(?:url|URL)$', url):
                            raise ExtractorError(
                                'Invalid URL:  %r . Call youtube-dl like this:  youtube-dl -v "https://www.youtube.com/watch?v=BaW_jenozKc"  ' % url,
                                expected=True)
                        else:
                            self._downloader.report_warning(
                                'Falling back to youtube search for  %s . Set --default-search "auto" to suppress this warning.' % url)
                    return self.url_result('ytsearch:' + url)

            if default_search in ('error', 'fixup_error'):
                raise ExtractorError(
                    '%r is not a valid URL. '
                    'Set --default-search "ytsearch" (or run  youtube-dl "ytsearch:%s" ) to search YouTube'
                    % (url, url), expected=True)
            else:
                if ':' not in default_search:
                    default_search += ':'
                return self.url_result(default_search + url)

        url, smuggled_data = unsmuggle_url(url)
        force_videoid = None
        is_intentional = smuggled_data and smuggled_data.get('to_generic')
        if smuggled_data and 'force_videoid' in smuggled_data:
            force_videoid = smuggled_data['force_videoid']
            video_id = force_videoid
        else:
            video_id = self._generic_id(url)

        self.to_screen('%s: Requesting header' % video_id)

        head_req = HEADRequest(url)
        head_response = self._request_webpage(
            head_req, video_id,
            note=False, errnote='Could not send HEAD request to %s' % url,
            fatal=False)

        if head_response is not False:
            # Check for redirect
            new_url = compat_str(head_response.geturl())
            if url != new_url:
                self.report_following_redirect(new_url)
                if force_videoid:
                    new_url = smuggle_url(
                        new_url, {'force_videoid': force_videoid})
                return self.url_result(new_url)

        full_response = None
        if head_response is False:
            request = sanitized_Request(url)
            request.add_header('Accept-Encoding', '*')
            full_response = self._request_webpage(request, video_id)
            head_response = full_response

        info_dict = {
            'id': video_id,
            'title': self._generic_title(url),
            'upload_date': unified_strdate(head_response.headers.get('Last-Modified'))
        }

        # Check for direct link to a video
        content_type = head_response.headers.get('Content-Type', '').lower()
        m = re.match(r'^(?P<type>audio|video|application(?=/(?:ogg$|(?:vnd\.apple\.|x-)?mpegurl)))/(?P<format_id>[^;\s]+)', content_type)
        if m:
            format_id = compat_str(m.group('format_id'))
            if format_id.endswith('mpegurl'):
                formats = self._extract_m3u8_formats(url, video_id, 'mp4')
            elif format_id == 'f4m':
                formats = self._extract_f4m_formats(url, video_id)
            else:
                formats = [{
                    'format_id': format_id,
                    'url': url,
                    'vcodec': 'none' if m.group('type') == 'audio' else None
                }]
                info_dict['direct'] = True
            self._sort_formats(formats)
            info_dict['formats'] = formats
            return info_dict

        if not self._downloader.params.get('test', False) and not is_intentional:
            force = self._downloader.params.get('force_generic_extractor', False)
            self._downloader.report_warning(
                '%s on generic information extractor.' % ('Forcing' if force else 'Falling back'))

        if not full_response:
            request = sanitized_Request(url)
            # Some webservers may serve compressed content of rather big size (e.g. gzipped flac)
            # making it impossible to download only chunk of the file (yet we need only 512kB to
            # test whether it's HTML or not). According to youtube-dl default Accept-Encoding
            # that will always result in downloading the whole file that is not desirable.
            # Therefore for extraction pass we have to override Accept-Encoding to any in order
            # to accept raw bytes and being able to download only a chunk.
            # It may probably better to solve this by checking Content-Type for application/octet-stream
            # after HEAD request finishes, but not sure if we can rely on this.
            request.add_header('Accept-Encoding', '*')
            full_response = self._request_webpage(request, video_id)

        first_bytes = full_response.read(512)

        # Is it an M3U playlist?
        if first_bytes.startswith(b'#EXTM3U'):
            info_dict['formats'] = self._extract_m3u8_formats(url, video_id, 'mp4')
            self._sort_formats(info_dict['formats'])
            return info_dict

        # Maybe it's a direct link to a video?
        # Be careful not to download the whole thing!
        if not is_html(first_bytes):
            self._downloader.report_warning(
                'URL could be a direct video link, returning it as such.')
            info_dict.update({
                'direct': True,
                'url': url,
            })
            return info_dict

        webpage = self._webpage_read_content(
            full_response, url, video_id, prefix=first_bytes)

        self.report_extraction(video_id)

        # Is it an RSS feed, a SMIL file, an XSPF playlist or a MPD manifest?
        try:
            doc = compat_etree_fromstring(webpage.encode('utf-8'))
            if doc.tag == 'rss':
                return self._extract_rss(url, video_id, doc)
            elif doc.tag == 'SmoothStreamingMedia':
                info_dict['formats'] = self._parse_ism_formats(doc, url)
                self._sort_formats(info_dict['formats'])
                return info_dict
            elif re.match(r'^(?:{[^}]+})?smil$', doc.tag):
                smil = self._parse_smil(doc, url, video_id)
                self._sort_formats(smil['formats'])
                return smil
            elif doc.tag == '{http://xspf.org/ns/0/}playlist':
                return self.playlist_result(
                    self._parse_xspf(
                        doc, video_id, xspf_url=url,
                        xspf_base_url=compat_str(full_response.geturl())),
                    video_id)
            elif re.match(r'(?i)^(?:{[^}]+})?MPD$', doc.tag):
                info_dict['formats'] = self._parse_mpd_formats(
                    doc,
                    mpd_base_url=compat_str(full_response.geturl()).rpartition('/')[0],
                    mpd_url=url)
                self._sort_formats(info_dict['formats'])
                return info_dict
            elif re.match(r'^{http://ns\.adobe\.com/f4m/[12]\.0}manifest$', doc.tag):
                info_dict['formats'] = self._parse_f4m_formats(doc, url, video_id)
                self._sort_formats(info_dict['formats'])
                return info_dict
        except compat_xml_parse_error:
            pass

        # Is it a Camtasia project?
        camtasia_res = self._extract_camtasia(url, video_id, webpage)
        if camtasia_res is not None:
            return camtasia_res

        # Sometimes embedded video player is hidden behind percent encoding
        # (e.g. https://github.com/ytdl-org/youtube-dl/issues/2448)
        # Unescaping the whole page allows to handle those cases in a generic way
        webpage = compat_urllib_parse_unquote(webpage)

        # Unescape squarespace embeds to be detected by generic extractor,
        # see https://github.com/ytdl-org/youtube-dl/issues/21294
        webpage = re.sub(
            r'<div[^>]+class=[^>]*?\bsqs-video-wrapper\b[^>]*>',
            lambda x: unescapeHTML(x.group(0)), webpage)

        # it's tempting to parse this further, but you would
        # have to take into account all the variations like
        #   Video Title - Site Name
        #   Site Name | Video Title
        #   Video Title - Tagline | Site Name
        # and so on and so forth; it's just not practical
        video_title = self._og_search_title(
            webpage, default=None) or self._html_search_regex(
            r'(?s)<title>(.*?)</title>', webpage, 'video title',
            default='video')

        # Try to detect age limit automatically
        age_limit = self._rta_search(webpage)
        # And then there are the jokers who advertise that they use RTA,
        # but actually don't.
        AGE_LIMIT_MARKERS = [
            r'Proudly Labeled <a href="http://www\.rtalabel\.org/" title="Restricted to Adults">RTA</a>',
        ]
        if any(re.search(marker, webpage) for marker in AGE_LIMIT_MARKERS):
            age_limit = 18

        # video uploader is domain name
        video_uploader = self._search_regex(
            r'^(?:https?://)?([^/]*)/.*', url, 'video uploader')

        video_description = self._og_search_description(webpage, default=None)
        video_thumbnail = self._og_search_thumbnail(webpage, default=None)

        info_dict.update({
            'title': video_title,
            'description': video_description,
            'thumbnail': video_thumbnail,
            'age_limit': age_limit,
        })

        # Look for Brightcove Legacy Studio embeds
        bc_urls = BrightcoveLegacyIE._extract_brightcove_urls(webpage)
        if bc_urls:
            entries = [{
                '_type': 'url',
                'url': smuggle_url(bc_url, {'Referer': url}),
                'ie_key': 'BrightcoveLegacy'
            } for bc_url in bc_urls]

            return {
                '_type': 'playlist',
                'title': video_title,
                'id': video_id,
                'entries': entries,
            }

        # Look for Brightcove New Studio embeds
        bc_urls = BrightcoveNewIE._extract_urls(self, webpage)
        if bc_urls:
            return self.playlist_from_matches(
                bc_urls, video_id, video_title,
                getter=lambda x: smuggle_url(x, {'referrer': url}),
                ie='BrightcoveNew')

        # Look for Nexx embeds
        nexx_urls = NexxIE._extract_urls(webpage)
        if nexx_urls:
            return self.playlist_from_matches(nexx_urls, video_id, video_title, ie=NexxIE.ie_key())

        # Look for Nexx iFrame embeds
        nexx_embed_urls = NexxEmbedIE._extract_urls(webpage)
        if nexx_embed_urls:
            return self.playlist_from_matches(nexx_embed_urls, video_id, video_title, ie=NexxEmbedIE.ie_key())

        # Look for ThePlatform embeds
        tp_urls = ThePlatformIE._extract_urls(webpage)
        if tp_urls:
            return self.playlist_from_matches(tp_urls, video_id, video_title, ie='ThePlatform')

        # Look for Vessel embeds
        vessel_urls = VesselIE._extract_urls(webpage)
        if vessel_urls:
            return self.playlist_from_matches(vessel_urls, video_id, video_title, ie=VesselIE.ie_key())

        # Look for embedded rtl.nl player
        matches = re.findall(
            r'<iframe[^>]+?src="((?:https?:)?//(?:(?:www|static)\.)?rtl\.nl/(?:system/videoplayer/[^"]+(?:video_)?)?embed[^"]+)"',
            webpage)
        if matches:
            return self.playlist_from_matches(matches, video_id, video_title, ie='RtlNl')

        vimeo_urls = VimeoIE._extract_urls(url, webpage)
        if vimeo_urls:
            return self.playlist_from_matches(vimeo_urls, video_id, video_title, ie=VimeoIE.ie_key())

        vid_me_embed_url = self._search_regex(
            r'src=[\'"](https?://vid\.me/[^\'"]+)[\'"]',
            webpage, 'vid.me embed', default=None)
        if vid_me_embed_url is not None:
            return self.url_result(vid_me_embed_url, 'Vidme')

        # Look for YouTube embeds
        youtube_urls = YoutubeIE._extract_urls(webpage)
        if youtube_urls:
            return self.playlist_from_matches(
                youtube_urls, video_id, video_title, ie=YoutubeIE.ie_key())

        matches = DailymotionIE._extract_urls(webpage)
        if matches:
            return self.playlist_from_matches(matches, video_id, video_title)

        # Look for embedded Dailymotion playlist player (#3822)
        m = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?dailymotion\.[a-z]{2,3}/widget/jukebox\?.+?)\1', webpage)
        if m:
            playlists = re.findall(
                r'list\[\]=/playlist/([^/]+)/', unescapeHTML(m.group('url')))
            if playlists:
                return self.playlist_from_matches(
                    playlists, video_id, video_title, lambda p: '//dailymotion.com/playlist/%s' % p)

        # Look for DailyMail embeds
        dailymail_urls = DailyMailIE._extract_urls(webpage)
        if dailymail_urls:
            return self.playlist_from_matches(
                dailymail_urls, video_id, video_title, ie=DailyMailIE.ie_key())

        # Look for embedded Wistia player
        wistia_url = WistiaIE._extract_url(webpage)
        if wistia_url:
            return {
                '_type': 'url_transparent',
                'url': self._proto_relative_url(wistia_url),
                'ie_key': WistiaIE.ie_key(),
                'uploader': video_uploader,
            }

        # Look for SVT player
        svt_url = SVTIE._extract_url(webpage)
        if svt_url:
            return self.url_result(svt_url, 'SVT')

        # Look for Bandcamp pages with custom domain
        mobj = re.search(r'<meta property="og:url"[^>]*?content="(.*?bandcamp\.com.*?)"', webpage)
        if mobj is not None:
            burl = unescapeHTML(mobj.group(1))
            # Don't set the extractor because it can be a track url or an album
            return self.url_result(burl)

        # Look for embedded Vevo player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:cache\.)?vevo\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for embedded Viddler player
        mobj = re.search(
            r'<(?:iframe[^>]+?src|param[^>]+?value)=(["\'])(?P<url>(?:https?:)?//(?:www\.)?viddler\.com/(?:embed|player)/.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for NYTimes player
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//graphics8\.nytimes\.com/bcvideo/[^/]+/iframe/embed\.html.+?)\1>',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for Libsyn player
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//html5-player\.libsyn\.com/embed/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for Ooyala videos
        mobj = (re.search(r'player\.ooyala\.com/[^"?]+[?#][^"]*?(?:embedCode|ec)=(?P<ec>[^"&]+)', webpage)
                or re.search(r'OO\.Player\.create\([\'"].*?[\'"],\s*[\'"](?P<ec>.{32})[\'"]', webpage)
                or re.search(r'OO\.Player\.create\.apply\(\s*OO\.Player\s*,\s*op\(\s*\[\s*[\'"][^\'"]*[\'"]\s*,\s*[\'"](?P<ec>.{32})[\'"]', webpage)
                or re.search(r'SBN\.VideoLinkset\.ooyala\([\'"](?P<ec>.{32})[\'"]\)', webpage)
                or re.search(r'data-ooyala-video-id\s*=\s*[\'"](?P<ec>.{32})[\'"]', webpage))
        if mobj is not None:
            embed_token = self._search_regex(
                r'embedToken[\'"]?\s*:\s*[\'"]([^\'"]+)',
                webpage, 'ooyala embed token', default=None)
            return OoyalaIE._build_url_result(smuggle_url(
                mobj.group('ec'), {
                    'domain': url,
                    'embed_token': embed_token,
                }))

        # Look for multiple Ooyala embeds on SBN network websites
        mobj = re.search(r'SBN\.VideoLinkset\.entryGroup\((\[.*?\])', webpage)
        if mobj is not None:
            embeds = self._parse_json(mobj.group(1), video_id, fatal=False)
            if embeds:
                return self.playlist_from_matches(
                    embeds, video_id, video_title,
                    getter=lambda v: OoyalaIE._url_for_embed_code(smuggle_url(v['provider_video_id'], {'domain': url})), ie='Ooyala')

        # Look for Aparat videos
        mobj = re.search(r'<iframe .*?src="(http://www\.aparat\.com/video/[^"]+)"', webpage)
        if mobj is not None:
            return self.url_result(mobj.group(1), 'Aparat')

        # Look for MPORA videos
        mobj = re.search(r'<iframe .*?src="(http://mpora\.(?:com|de)/videos/[^"]+)"', webpage)
        if mobj is not None:
            return self.url_result(mobj.group(1), 'Mpora')

        # Look for embedded Facebook player
        facebook_urls = FacebookIE._extract_urls(webpage)
        if facebook_urls:
            return self.playlist_from_matches(facebook_urls, video_id, video_title)

        # Look for embedded VK player
        mobj = re.search(r'<iframe[^>]+?src=(["\'])(?P<url>https?://vk\.com/video_ext\.php.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'VK')

        # Look for embedded Odnoklassniki player
        mobj = re.search(r'<iframe[^>]+?src=(["\'])(?P<url>https?://(?:odnoklassniki|ok)\.ru/videoembed/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Odnoklassniki')

        # Look for embedded ivi player
        mobj = re.search(r'<embed[^>]+?src=(["\'])(?P<url>https?://(?:www\.)?ivi\.ru/video/player.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Ivi')

        # Look for embedded Huffington Post player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://embed\.live\.huffingtonpost\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'HuffPost')

        # Look for embed.ly
        mobj = re.search(r'class=["\']embedly-card["\'][^>]href=["\'](?P<url>[^"\']+)', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))
        mobj = re.search(r'class=["\']embedly-embed["\'][^>]src=["\'][^"\']*url=(?P<url>[^&]+)', webpage)
        if mobj is not None:
            return self.url_result(compat_urllib_parse_unquote(mobj.group('url')))

        # Look for funnyordie embed
        matches = re.findall(r'<iframe[^>]+?src="(https?://(?:www\.)?funnyordie\.com/embed/[^"]+)"', webpage)
        if matches:
            return self.playlist_from_matches(
                matches, video_id, video_title, getter=unescapeHTML, ie='FunnyOrDie')

        # Look for BBC iPlayer embed
        matches = re.findall(r'setPlaylist\("(https?://www\.bbc\.co\.uk/iplayer/[^/]+/[\da-z]{8})"\)', webpage)
        if matches:
            return self.playlist_from_matches(matches, video_id, video_title, ie='BBCCoUk')

        # Look for embedded RUTV player
        rutv_url = RUTVIE._extract_url(webpage)
        if rutv_url:
            return self.url_result(rutv_url, 'RUTV')

        # Look for embedded TVC player
        tvc_url = TVCIE._extract_url(webpage)
        if tvc_url:
            return self.url_result(tvc_url, 'TVC')

        # Look for embedded SportBox player
        sportbox_urls = SportBoxIE._extract_urls(webpage)
        if sportbox_urls:
            return self.playlist_from_matches(sportbox_urls, video_id, video_title, ie=SportBoxIE.ie_key())

        # Look for embedded XHamster player
        xhamster_urls = XHamsterEmbedIE._extract_urls(webpage)
        if xhamster_urls:
            return self.playlist_from_matches(xhamster_urls, video_id, video_title, ie='XHamsterEmbed')

        # Look for embedded TNAFlixNetwork player
        tnaflix_urls = TNAFlixNetworkEmbedIE._extract_urls(webpage)
        if tnaflix_urls:
            return self.playlist_from_matches(tnaflix_urls, video_id, video_title, ie=TNAFlixNetworkEmbedIE.ie_key())

        # Look for embedded PornHub player
        pornhub_urls = PornHubIE._extract_urls(webpage)
        if pornhub_urls:
            return self.playlist_from_matches(pornhub_urls, video_id, video_title, ie=PornHubIE.ie_key())

        # Look for embedded DrTuber player
        drtuber_urls = DrTuberIE._extract_urls(webpage)
        if drtuber_urls:
            return self.playlist_from_matches(drtuber_urls, video_id, video_title, ie=DrTuberIE.ie_key())

        # Look for embedded RedTube player
        redtube_urls = RedTubeIE._extract_urls(webpage)
        if redtube_urls:
            return self.playlist_from_matches(redtube_urls, video_id, video_title, ie=RedTubeIE.ie_key())

        # Look for embedded Tube8 player
        tube8_urls = Tube8IE._extract_urls(webpage)
        if tube8_urls:
            return self.playlist_from_matches(tube8_urls, video_id, video_title, ie=Tube8IE.ie_key())

        # Look for embedded Tvigle player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//cloud\.tvigle\.ru/video/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Tvigle')

        # Look for embedded TED player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://embed(?:-ssl)?\.ted\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'TED')

        # Look for embedded Ustream videos
        ustream_url = UstreamIE._extract_url(webpage)
        if ustream_url:
            return self.url_result(ustream_url, UstreamIE.ie_key())

        # Look for embedded arte.tv player
        mobj = re.search(
            r'<(?:script|iframe) [^>]*?src="(?P<url>http://www\.arte\.tv/(?:playerv2/embed|arte_vp/index)[^"]+)"',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'ArteTVEmbed')

        # Look for embedded francetv player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?://)?embed\.francetv\.fr/\?ue=.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for embedded smotri.com player
        smotri_url = SmotriIE._extract_url(webpage)
        if smotri_url:
            return self.url_result(smotri_url, 'Smotri')

        # Look for embedded Myvi.ru player
        myvi_url = MyviIE._extract_url(webpage)
        if myvi_url:
            return self.url_result(myvi_url)

        # Look for embedded soundcloud player
        soundcloud_urls = SoundcloudIE._extract_urls(webpage)
        if soundcloud_urls:
            return self.playlist_from_matches(soundcloud_urls, video_id, video_title, getter=unescapeHTML, ie=SoundcloudIE.ie_key())

        # Look for tunein player
        tunein_urls = TuneInBaseIE._extract_urls(webpage)
        if tunein_urls:
            return self.playlist_from_matches(tunein_urls, video_id, video_title)

        # Look for embedded mtvservices player
        mtvservices_url = MTVServicesEmbeddedIE._extract_url(webpage)
        if mtvservices_url:
            return self.url_result(mtvservices_url, ie='MTVServicesEmbedded')

        # Look for embedded yahoo player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://(?:screen|movies)\.yahoo\.com/.+?\.html\?format=embed)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Yahoo')

        # Look for embedded sbs.com.au player
        mobj = re.search(
            r'''(?x)
            (?:
                <meta\s+property="og:video"\s+content=|
                <iframe[^>]+?src=
            )
            (["\'])(?P<url>https?://(?:www\.)?sbs\.com\.au/ondemand/video/.+?)\1''',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'SBS')

        # Look for embedded Cinchcast player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://player\.cinchcast\.com/.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Cinchcast')

        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://m(?:lb)?\.mlb\.com/shared/video/embed/embed\.html\?.+?)\1',
            webpage)
        if not mobj:
            mobj = re.search(
                r'data-video-link=["\'](?P<url>http://m.mlb.com/video/[^"\']+)',
                webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'MLB')

        mobj = re.search(
            r'<(?:iframe|script)[^>]+?src=(["\'])(?P<url>%s)\1' % CondeNastIE.EMBED_URL,
            webpage)
        if mobj is not None:
            return self.url_result(self._proto_relative_url(mobj.group('url'), scheme='http:'), 'CondeNast')

        mobj = re.search(
            r'<iframe[^>]+src="(?P<url>https?://(?:new\.)?livestream\.com/[^"]+/player[^"]+)"',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Livestream')

        # Look for Zapiks embed
        mobj = re.search(
            r'<iframe[^>]+src="(?P<url>https?://(?:www\.)?zapiks\.fr/index\.php\?.+?)"', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Zapiks')

        # Look for Kaltura embeds
        kaltura_url = KalturaIE._extract_url(webpage)
        if kaltura_url:
            return self.url_result(smuggle_url(kaltura_url, {'source_url': url}), KalturaIE.ie_key())

        # Look for EaglePlatform embeds
        eagleplatform_url = EaglePlatformIE._extract_url(webpage)
        if eagleplatform_url:
            return self.url_result(smuggle_url(eagleplatform_url, {'referrer': url}), EaglePlatformIE.ie_key())

        # Look for ClipYou (uses EaglePlatform) embeds
        mobj = re.search(
            r'<iframe[^>]+src="https?://(?P<host>media\.clipyou\.ru)/index/player\?.*\brecord_id=(?P<id>\d+).*"', webpage)
        if mobj is not None:
            return self.url_result('eagleplatform:%(host)s:%(id)s' % mobj.groupdict(), 'EaglePlatform')

        # Look for Pladform embeds
        pladform_url = PladformIE._extract_url(webpage)
        if pladform_url:
            return self.url_result(pladform_url)

        # Look for Videomore embeds
        videomore_url = VideomoreIE._extract_url(webpage)
        if videomore_url:
            return self.url_result(videomore_url)

        # Look for Webcaster embeds
        webcaster_url = WebcasterFeedIE._extract_url(self, webpage)
        if webcaster_url:
            return self.url_result(webcaster_url, ie=WebcasterFeedIE.ie_key())

        # Look for Playwire embeds
        mobj = re.search(
            r'<script[^>]+data-config=(["\'])(?P<url>(?:https?:)?//config\.playwire\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for 5min embeds
        mobj = re.search(
            r'<meta[^>]+property="og:video"[^>]+content="https?://embed\.5min\.com/(?P<id>[0-9]+)/?', webpage)
        if mobj is not None:
            return self.url_result('5min:%s' % mobj.group('id'), 'FiveMin')

        # Look for Crooks and Liars embeds
        mobj = re.search(
            r'<(?:iframe[^>]+src|param[^>]+value)=(["\'])(?P<url>(?:https?:)?//embed\.crooksandliars\.com/(?:embed|v)/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for NBC Sports VPlayer embeds
        nbc_sports_url = NBCSportsVPlayerIE._extract_url(webpage)
        if nbc_sports_url:
            return self.url_result(nbc_sports_url, 'NBCSportsVPlayer')

        # Look for NBC News embeds
        nbc_news_embed_url = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//www\.nbcnews\.com/widget/video-embed/[^"\']+)\1', webpage)
        if nbc_news_embed_url:
            return self.url_result(nbc_news_embed_url.group('url'), 'NBCNews')

        # Look for Google Drive embeds
        google_drive_url = GoogleDriveIE._extract_url(webpage)
        if google_drive_url:
            return self.url_result(google_drive_url, 'GoogleDrive')

        # Look for UDN embeds
        mobj = re.search(
            r'<iframe[^>]+src="(?:https?:)?(?P<url>%s)"' % UDNEmbedIE._PROTOCOL_RELATIVE_VALID_URL, webpage)
        if mobj is not None:
            return self.url_result(
                compat_urlparse.urljoin(url, mobj.group('url')), 'UDNEmbed')

        # Look for Senate ISVP iframe
        senate_isvp_url = SenateISVPIE._search_iframe_url(webpage)
        if senate_isvp_url:
            return self.url_result(senate_isvp_url, 'SenateISVP')

        # Look for OnionStudios embeds
        onionstudios_url = OnionStudiosIE._extract_url(webpage)
        if onionstudios_url:
            return self.url_result(onionstudios_url)

        # Look for ViewLift embeds
        viewlift_url = ViewLiftEmbedIE._extract_url(webpage)
        if viewlift_url:
            return self.url_result(viewlift_url)

        # Look for JWPlatform embeds
        jwplatform_urls = JWPlatformIE._extract_urls(webpage)
        if jwplatform_urls:
            return self.playlist_from_matches(jwplatform_urls, video_id, video_title, ie=JWPlatformIE.ie_key())

        # Look for Digiteka embeds
        digiteka_url = DigitekaIE._extract_url(webpage)
        if digiteka_url:
            return self.url_result(self._proto_relative_url(digiteka_url), DigitekaIE.ie_key())

        # Look for Arkena embeds
        arkena_url = ArkenaIE._extract_url(webpage)
        if arkena_url:
            return self.url_result(arkena_url, ArkenaIE.ie_key())

        # Look for Piksel embeds
        piksel_url = PikselIE._extract_url(webpage)
        if piksel_url:
            return self.url_result(piksel_url, PikselIE.ie_key())

        # Look for Limelight embeds
        limelight_urls = LimelightBaseIE._extract_urls(webpage, url)
        if limelight_urls:
            return self.playlist_result(
                limelight_urls, video_id, video_title, video_description)

        # Look for Anvato embeds
        anvato_urls = AnvatoIE._extract_urls(self, webpage, video_id)
        if anvato_urls:
            return self.playlist_result(
                anvato_urls, video_id, video_title, video_description)

        # Look for AdobeTVVideo embeds
        mobj = re.search(
            r'<iframe[^>]+src=[\'"]((?:https?:)?//video\.tv\.adobe\.com/v/\d+[^"]+)[\'"]',
            webpage)
        if mobj is not None:
            return self.url_result(
                self._proto_relative_url(unescapeHTML(mobj.group(1))),
                'AdobeTVVideo')

        # Look for Vine embeds
        mobj = re.search(
            r'<iframe[^>]+src=[\'"]((?:https?:)?//(?:www\.)?vine\.co/v/[^/]+/embed/(?:simple|postcard))',
            webpage)
        if mobj is not None:
            return self.url_result(
                self._proto_relative_url(unescapeHTML(mobj.group(1))), 'Vine')

        # Look for VODPlatform embeds
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?vod-platform\.net/[eE]mbed/.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(
                self._proto_relative_url(unescapeHTML(mobj.group('url'))), 'VODPlatform')

        # Look for Mangomolo embeds
        mobj = re.search(
            r'''(?x)<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?admin\.mangomolo\.com/analytics/index\.php/customers/embed/
                (?:
                    video\?.*?\bid=(?P<video_id>\d+)|
                    index\?.*?\bchannelid=(?P<channel_id>(?:[A-Za-z0-9+/=]|%2B|%2F|%3D)+)
                ).+?)\1''', webpage)
        if mobj is not None:
            info = {
                '_type': 'url_transparent',
                'url': self._proto_relative_url(unescapeHTML(mobj.group('url'))),
                'title': video_title,
                'description': video_description,
                'thumbnail': video_thumbnail,
                'uploader': video_uploader,
            }
            video_id = mobj.group('video_id')
            if video_id:
                info.update({
                    'ie_key': 'MangomoloVideo',
                    'id': video_id,
                })
            else:
                info.update({
                    'ie_key': 'MangomoloLive',
                    'id': mobj.group('channel_id'),
                })
            return info

        # Look for Instagram embeds
        instagram_embed_url = InstagramIE._extract_embed_url(webpage)
        if instagram_embed_url is not None:
            return self.url_result(
                self._proto_relative_url(instagram_embed_url), InstagramIE.ie_key())

        # Look for LiveLeak embeds
        liveleak_urls = LiveLeakIE._extract_urls(webpage)
        if liveleak_urls:
            return self.playlist_from_matches(liveleak_urls, video_id, video_title)

        # Look for 3Q SDN embeds
        threeqsdn_url = ThreeQSDNIE._extract_url(webpage)
        if threeqsdn_url:
            return {
                '_type': 'url_transparent',
                'ie_key': ThreeQSDNIE.ie_key(),
                'url': self._proto_relative_url(threeqsdn_url),
                'title': video_title,
                'description': video_description,
                'thumbnail': video_thumbnail,
                'uploader': video_uploader,
            }

        # Look for VBOX7 embeds
        vbox7_url = Vbox7IE._extract_url(webpage)
        if vbox7_url:
            return self.url_result(vbox7_url, Vbox7IE.ie_key())

        # Look for DBTV embeds
        dbtv_urls = DBTVIE._extract_urls(webpage)
        if dbtv_urls:
            return self.playlist_from_matches(dbtv_urls, video_id, video_title, ie=DBTVIE.ie_key())

        # Look for Videa embeds
        videa_urls = VideaIE._extract_urls(webpage)
        if videa_urls:
            return self.playlist_from_matches(videa_urls, video_id, video_title, ie=VideaIE.ie_key())

        # Look for 20 minuten embeds
        twentymin_urls = TwentyMinutenIE._extract_urls(webpage)
        if twentymin_urls:
            return self.playlist_from_matches(
                twentymin_urls, video_id, video_title, ie=TwentyMinutenIE.ie_key())

        # Look for Openload embeds
        openload_urls = OpenloadIE._extract_urls(webpage)
        if openload_urls:
            return self.playlist_from_matches(
                openload_urls, video_id, video_title, ie=OpenloadIE.ie_key())

        # Look for Verystream embeds
        verystream_urls = VerystreamIE._extract_urls(webpage)
        if verystream_urls:
            return self.playlist_from_matches(
                verystream_urls, video_id, video_title, ie=VerystreamIE.ie_key())

        # Look for VideoPress embeds
        videopress_urls = VideoPressIE._extract_urls(webpage)
        if videopress_urls:
            return self.playlist_from_matches(
                videopress_urls, video_id, video_title, ie=VideoPressIE.ie_key())

        # Look for Rutube embeds
        rutube_urls = RutubeIE._extract_urls(webpage)
        if rutube_urls:
            return self.playlist_from_matches(
                rutube_urls, video_id, video_title, ie=RutubeIE.ie_key())

        # Look for WashingtonPost embeds
        wapo_urls = WashingtonPostIE._extract_urls(webpage)
        if wapo_urls:
            return self.playlist_from_matches(
                wapo_urls, video_id, video_title, ie=WashingtonPostIE.ie_key())

        # Look for Mediaset embeds
        mediaset_urls = MediasetIE._extract_urls(self, webpage)
        if mediaset_urls:
            return self.playlist_from_matches(
                mediaset_urls, video_id, video_title, ie=MediasetIE.ie_key())

        # Look for JOJ.sk embeds
        joj_urls = JojIE._extract_urls(webpage)
        if joj_urls:
            return self.playlist_from_matches(
                joj_urls, video_id, video_title, ie=JojIE.ie_key())

        # Look for megaphone.fm embeds
        mpfn_urls = MegaphoneIE._extract_urls(webpage)
        if mpfn_urls:
            return self.playlist_from_matches(
                mpfn_urls, video_id, video_title, ie=MegaphoneIE.ie_key())

        # Look for vzaar embeds
        vzaar_urls = VzaarIE._extract_urls(webpage)
        if vzaar_urls:
            return self.playlist_from_matches(
                vzaar_urls, video_id, video_title, ie=VzaarIE.ie_key())

        channel9_urls = Channel9IE._extract_urls(webpage)
        if channel9_urls:
            return self.playlist_from_matches(
                channel9_urls, video_id, video_title, ie=Channel9IE.ie_key())

        vshare_urls = VShareIE._extract_urls(webpage)
        if vshare_urls:
            return self.playlist_from_matches(
                vshare_urls, video_id, video_title, ie=VShareIE.ie_key())

        # Look for Mediasite embeds
        mediasite_urls = MediasiteIE._extract_urls(webpage)
        if mediasite_urls:
            entries = [
                self.url_result(smuggle_url(
                    compat_urlparse.urljoin(url, mediasite_url),
                    {'UrlReferrer': url}), ie=MediasiteIE.ie_key())
                for mediasite_url in mediasite_urls]
            return self.playlist_result(entries, video_id, video_title)

        springboardplatform_urls = SpringboardPlatformIE._extract_urls(webpage)
        if springboardplatform_urls:
            return self.playlist_from_matches(
                springboardplatform_urls, video_id, video_title,
                ie=SpringboardPlatformIE.ie_key())

        yapfiles_urls = YapFilesIE._extract_urls(webpage)
        if yapfiles_urls:
            return self.playlist_from_matches(
                yapfiles_urls, video_id, video_title, ie=YapFilesIE.ie_key())

        vice_urls = ViceIE._extract_urls(webpage)
        if vice_urls:
            return self.playlist_from_matches(
                vice_urls, video_id, video_title, ie=ViceIE.ie_key())

        xfileshare_urls = XFileShareIE._extract_urls(webpage)
        if xfileshare_urls:
            return self.playlist_from_matches(
                xfileshare_urls, video_id, video_title, ie=XFileShareIE.ie_key())

        cloudflarestream_urls = CloudflareStreamIE._extract_urls(webpage)
        if cloudflarestream_urls:
            return self.playlist_from_matches(
                cloudflarestream_urls, video_id, video_title, ie=CloudflareStreamIE.ie_key())

        peertube_urls = PeerTubeIE._extract_urls(webpage, url)
        if peertube_urls:
            return self.playlist_from_matches(
                peertube_urls, video_id, video_title, ie=PeerTubeIE.ie_key())

        teachable_url = TeachableIE._extract_url(webpage, url)
        if teachable_url:
            return self.url_result(teachable_url)

        indavideo_urls = IndavideoEmbedIE._extract_urls(webpage)
        if indavideo_urls:
            return self.playlist_from_matches(
                indavideo_urls, video_id, video_title, ie=IndavideoEmbedIE.ie_key())

        apa_urls = APAIE._extract_urls(webpage)
        if apa_urls:
            return self.playlist_from_matches(
                apa_urls, video_id, video_title, ie=APAIE.ie_key())

        foxnews_urls = FoxNewsIE._extract_urls(webpage)
        if foxnews_urls:
            return self.playlist_from_matches(
                foxnews_urls, video_id, video_title, ie=FoxNewsIE.ie_key())

        sharevideos_urls = [sharevideos_mobj.group('url') for sharevideos_mobj in re.finditer(
            r'<iframe[^>]+?\bsrc\s*=\s*(["\'])(?P<url>(?:https?:)?//embed\.share-videos\.se/auto/embed/\d+\?.*?\buid=\d+.*?)\1',
            webpage)]
        if sharevideos_urls:
            return self.playlist_from_matches(
                sharevideos_urls, video_id, video_title)

        viqeo_urls = ViqeoIE._extract_urls(webpage)
        if viqeo_urls:
            return self.playlist_from_matches(
                viqeo_urls, video_id, video_title, ie=ViqeoIE.ie_key())

        expressen_urls = ExpressenIE._extract_urls(webpage)
        if expressen_urls:
            return self.playlist_from_matches(
                expressen_urls, video_id, video_title, ie=ExpressenIE.ie_key())

        zype_urls = ZypeIE._extract_urls(webpage)
        if zype_urls:
            return self.playlist_from_matches(
                zype_urls, video_id, video_title, ie=ZypeIE.ie_key())

        # Look for HTML5 media
        entries = self._parse_html5_media_entries(url, webpage, video_id, m3u8_id='hls')
        if entries:
            if len(entries) == 1:
                entries[0].update({
                    'id': video_id,
                    'title': video_title,
                })
            else:
                for num, entry in enumerate(entries, start=1):
                    entry.update({
                        'id': '%s-%s' % (video_id, num),
                        'title': '%s (%d)' % (video_title, num),
                    })
            for entry in entries:
                self._sort_formats(entry['formats'])
            return self.playlist_result(entries, video_id, video_title)

        jwplayer_data = self._find_jwplayer_data(
            webpage, video_id, transform_source=js_to_json)
        if jwplayer_data:
            try:
                info = self._parse_jwplayer_data(
                    jwplayer_data, video_id, require_title=False, base_url=url)
                return merge_dicts(info, info_dict)
            except ExtractorError:
                # See https://github.com/ytdl-org/youtube-dl/pull/16735
                pass

        # Video.js embed
        mobj = re.search(
            r'(?s)\bvideojs\s*\(.+?\.src\s*\(\s*((?:\[.+?\]|{.+?}))\s*\)\s*;',
            webpage)
        if mobj is not None:
            sources = self._parse_json(
                mobj.group(1), video_id, transform_source=js_to_json,
                fatal=False) or []
            if not isinstance(sources, list):
                sources = [sources]
            formats = []
            for source in sources:
                src = source.get('src')
                if not src or not isinstance(src, compat_str):
                    continue
                src = compat_urlparse.urljoin(url, src)
                src_type = source.get('type')
                if isinstance(src_type, compat_str):
                    src_type = src_type.lower()
                ext = determine_ext(src).lower()
                if src_type == 'video/youtube':
                    return self.url_result(src, YoutubeIE.ie_key())
                if src_type == 'application/dash+xml' or ext == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        src, video_id, mpd_id='dash', fatal=False))
                elif src_type == 'application/x-mpegurl' or ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        src, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=False))
                else:
                    formats.append({
                        'url': src,
                        'ext': (mimetype2ext(src_type)
                                or ext if ext in KNOWN_EXTENSIONS else 'mp4'),
                    })
            if formats:
                self._sort_formats(formats)
                info_dict['formats'] = formats
                return info_dict

        # Looking for http://schema.org/VideoObject
        json_ld = self._search_json_ld(
            webpage, video_id, default={}, expected_type='VideoObject')
        if json_ld.get('url'):
            return merge_dicts(json_ld, info_dict)

        def check_video(vurl):
            if YoutubeIE.suitable(vurl):
                return True
            if RtmpIE.suitable(vurl):
                return True
            vpath = compat_urlparse.urlparse(vurl).path
            vext = determine_ext(vpath)
            return '.' in vpath and vext not in ('swf', 'png', 'jpg', 'srt', 'sbv', 'sub', 'vtt', 'ttml', 'js', 'xml')

        def filter_video(urls):
            return list(filter(check_video, urls))

        # Start with something easy: JW Player in SWFObject
        found = filter_video(re.findall(r'flashvars: [\'"](?:.*&)?file=(http[^\'"&]*)', webpage))
        if not found:
            # Look for gorilla-vid style embedding
            found = filter_video(re.findall(r'''(?sx)
                (?:
                    jw_plugins|
                    JWPlayerOptions|
                    jwplayer\s*\(\s*["'][^'"]+["']\s*\)\s*\.setup
                )
                .*?
                ['"]?file['"]?\s*:\s*["\'](.*?)["\']''', webpage))
        if not found:
            # Broaden the search a little bit
            found = filter_video(re.findall(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage))
        if not found:
            # Broaden the findall a little bit: JWPlayer JS loader
            found = filter_video(re.findall(
                r'[^A-Za-z0-9]?(?:file|video_url)["\']?:\s*["\'](http(?![^\'"]+\.[0-9]+[\'"])[^\'"]+)["\']', webpage))
        if not found:
            # Flow player
            found = filter_video(re.findall(r'''(?xs)
                flowplayer\("[^"]+",\s*
                    \{[^}]+?\}\s*,
                    \s*\{[^}]+? ["']?clip["']?\s*:\s*\{\s*
                        ["']?url["']?\s*:\s*["']([^"']+)["']
            ''', webpage))
        if not found:
            # Cinerama player
            found = re.findall(
                r"cinerama\.embedPlayer\(\s*\'[^']+\',\s*'([^']+)'", webpage)
        if not found:
            # Try to find twitter cards info
            # twitter:player:stream should be checked before twitter:player since
            # it is expected to contain a raw stream (see
            # https://dev.twitter.com/cards/types/player#On_twitter.com_via_desktop_browser)
            found = filter_video(re.findall(
                r'<meta (?:property|name)="twitter:player:stream" (?:content|value)="(.+?)"', webpage))
        if not found:
            # We look for Open Graph info:
            # We have to match any number spaces between elements, some sites try to align them (eg.: statigr.am)
            m_video_type = re.findall(r'<meta.*?property="og:video:type".*?content="video/(.*?)"', webpage)
            # We only look in og:video if the MIME type is a video, don't try if it's a Flash player:
            if m_video_type is not None:
                found = filter_video(re.findall(r'<meta.*?property="og:video".*?content="(.*?)"', webpage))
        if not found:
            REDIRECT_REGEX = r'[0-9]{,2};\s*(?:URL|url)=\'?([^\'"]+)'
            found = re.search(
                r'(?i)<meta\s+(?=(?:[a-z-]+="[^"]+"\s+)*http-equiv="refresh")'
                r'(?:[a-z-]+="[^"]+"\s+)*?content="%s' % REDIRECT_REGEX,
                webpage)
            if not found:
                # Look also in Refresh HTTP header
                refresh_header = head_response.headers.get('Refresh')
                if refresh_header:
                    # In python 2 response HTTP headers are bytestrings
                    if sys.version_info < (3, 0) and isinstance(refresh_header, str):
                        refresh_header = refresh_header.decode('iso-8859-1')
                    found = re.search(REDIRECT_REGEX, refresh_header)
            if found:
                new_url = compat_urlparse.urljoin(url, unescapeHTML(found.group(1)))
                if new_url != url:
                    self.report_following_redirect(new_url)
                    return {
                        '_type': 'url',
                        'url': new_url,
                    }
                else:
                    found = None

        if not found:
            # twitter:player is a https URL to iframe player that may or may not
            # be supported by youtube-dl thus this is checked the very last (see
            # https://dev.twitter.com/cards/types/player#On_twitter.com_via_desktop_browser)
            embed_url = self._html_search_meta('twitter:player', webpage, default=None)
            if embed_url and embed_url != url:
                return self.url_result(embed_url)

        if not found:
            raise UnsupportedError(url)

        entries = []
        for video_url in orderedSet(found):
            video_url = unescapeHTML(video_url)
            video_url = video_url.replace('\\/', '/')
            video_url = compat_urlparse.urljoin(url, video_url)
            video_id = compat_urllib_parse_unquote(os.path.basename(video_url))

            # Sometimes, jwplayer extraction will result in a YouTube URL
            if YoutubeIE.suitable(video_url):
                entries.append(self.url_result(video_url, 'Youtube'))
                continue

            # here's a fun little line of code for you:
            video_id = os.path.splitext(video_id)[0]

            entry_info_dict = {
                'id': video_id,
                'uploader': video_uploader,
                'title': video_title,
                'age_limit': age_limit,
            }

            if RtmpIE.suitable(video_url):
                entry_info_dict.update({
                    '_type': 'url_transparent',
                    'ie_key': RtmpIE.ie_key(),
                    'url': video_url,
                })
                entries.append(entry_info_dict)
                continue

            ext = determine_ext(video_url)
            if ext == 'smil':
                entry_info_dict['formats'] = self._extract_smil_formats(video_url, video_id)
            elif ext == 'xspf':
                return self.playlist_result(self._extract_xspf_playlist(video_url, video_id), video_id)
            elif ext == 'm3u8':
                entry_info_dict['formats'] = self._extract_m3u8_formats(video_url, video_id, ext='mp4')
            elif ext == 'mpd':
                entry_info_dict['formats'] = self._extract_mpd_formats(video_url, video_id)
            elif ext == 'f4m':
                entry_info_dict['formats'] = self._extract_f4m_formats(video_url, video_id)
            elif re.search(r'(?i)\.(?:ism|smil)/manifest', video_url) and video_url != url:
                # Just matching .ism/manifest is not enough to be reliably sure
                # whether it's actually an ISM manifest or some other streaming
                # manifest since there are various streaming URL formats
                # possible (see [1]) as well as some other shenanigans like
                # .smil/manifest URLs that actually serve an ISM (see [2]) and
                # so on.
                # Thus the most reasonable way to solve this is to delegate
                # to generic extractor in order to look into the contents of
                # the manifest itself.
                # 1. https://azure.microsoft.com/en-us/documentation/articles/media-services-deliver-content-overview/#streaming-url-formats
                # 2. https://svs.itworkscdn.net/lbcivod/smil:itwfcdn/lbci/170976.smil/Manifest
                entry_info_dict = self.url_result(
                    smuggle_url(video_url, {'to_generic': True}),
                    GenericIE.ie_key())
            else:
                entry_info_dict['url'] = video_url

            if entry_info_dict.get('formats'):
                self._sort_formats(entry_info_dict['formats'])

            entries.append(entry_info_dict)

        if len(entries) == 1:
            return entries[0]
        else:
            for num, e in enumerate(entries, start=1):
                # 'url' results don't have a title
                if e.get('title') is not None:
                    e['title'] = '%s (%d)' % (e['title'], num)
            return {
                '_type': 'playlist',
                'entries': entries,
            }
