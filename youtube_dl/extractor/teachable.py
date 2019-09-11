from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .wistia import WistiaIE
from ..compat import compat_str
from ..utils import (
    clean_html,
    ExtractorError,
    get_element_by_class,
    urlencode_postdata,
    urljoin,
)


class TeachableBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'teachable'
    _URL_PREFIX = 'teachable:'

    _SITES = {
        # Only notable ones here
        'upskillcourses.com': 'upskill',
        'academy.gns3.com': 'gns3',
        'academyhacker.com': 'academyhacker',
        'stackskills.com': 'stackskills',
        'market.saleshacker.com': 'saleshacker',
        'learnability.org': 'learnability',
        'edurila.com': 'edurila',
        'courses.workitdaily.com': 'workitdaily',
    }

    _VALID_URL_SUB_TUPLE = (_URL_PREFIX, '|'.join(re.escape(site) for site in _SITES.keys()))

    def _real_initialize(self):
        self._logged_in = False

    def _login(self, site):
        if self._logged_in:
            return

        username, password = self._get_login_info(
            netrc_machine=self._SITES.get(site, site))
        if username is None:
            return

        login_page, urlh = self._download_webpage_handle(
            'https://%s/sign_in' % site, None,
            'Downloading %s login page' % site)

        login_url = compat_str(urlh.geturl())

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'user[email]': username,
            'user[password]': password,
        })

        post_url = self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>(?:(?!\1).)+)\1', login_page,
            'post url', default=login_url, group='url')

        if not post_url.startswith('http'):
            post_url = urljoin(login_url, post_url)

        response = self._download_webpage(
            post_url, None, 'Logging in to %s' % site,
            data=urlencode_postdata(login_form),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': login_url,
            })

        if '>I accept the new Privacy Policy<' in response:
            raise ExtractorError(
                'Unable to login: %s asks you to accept new Privacy Policy. '
                'Go to https://%s/ and accept.' % (site, site), expected=True)

        # Successful login
        if any(re.search(p, response) for p in (
                r'class=["\']user-signout',
                r'<a[^>]+\bhref=["\']/sign_out',
                r'>\s*Log out\s*<')):
            self._logged_in = True
            return

        message = get_element_by_class('alert', response)
        if message is not None:
            raise ExtractorError(
                'Unable to login: %s' % clean_html(message), expected=True)

        raise ExtractorError('Unable to log in')


class TeachableIE(TeachableBaseIE):
    _VALID_URL = r'''(?x)
                    (?:
                        %shttps?://(?P<site_t>[^/]+)|
                        https?://(?:www\.)?(?P<site>%s)
                    )
                    /courses/[^/]+/lectures/(?P<id>\d+)
                    ''' % TeachableBaseIE._VALID_URL_SUB_TUPLE

    _TESTS = [{
        'url': 'http://upskillcourses.com/courses/essential-web-developer-course/lectures/1747100',
        'info_dict': {
            'id': 'uzw6zw58or',
            'ext': 'mp4',
            'title': 'Welcome to the Course!',
            'description': 'md5:65edb0affa582974de4625b9cdea1107',
            'duration': 138.763,
            'timestamp': 1479846621,
            'upload_date': '20161122',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://upskillcourses.com/courses/119763/lectures/1747100',
        'only_matching': True,
    }, {
        'url': 'https://academy.gns3.com/courses/423415/lectures/6885939',
        'only_matching': True,
    }, {
        'url': 'teachable:https://upskillcourses.com/courses/essential-web-developer-course/lectures/1747100',
        'only_matching': True,
    }]

    @staticmethod
    def _is_teachable(webpage):
        return 'teachableTracker.linker:autoLink' in webpage and re.search(
            r'<link[^>]+href=["\']https?://process\.fs\.teachablecdn\.com',
            webpage)

    @staticmethod
    def _extract_url(webpage, source_url):
        if not TeachableIE._is_teachable(webpage):
            return
        if re.match(r'https?://[^/]+/(?:courses|p)', source_url):
            return '%s%s' % (TeachableBaseIE._URL_PREFIX, source_url)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site = mobj.group('site') or mobj.group('site_t')
        video_id = mobj.group('id')

        self._login(site)

        prefixed = url.startswith(self._URL_PREFIX)
        if prefixed:
            url = url[len(self._URL_PREFIX):]

        webpage = self._download_webpage(url, video_id)

        wistia_url = WistiaIE._extract_url(webpage)
        if not wistia_url:
            if any(re.search(p, webpage) for p in (
                    r'class=["\']lecture-contents-locked',
                    r'>\s*Lecture contents locked',
                    r'id=["\']lecture-locked')):
                self.raise_login_required('Lecture contents locked')

        title = self._og_search_title(webpage, default=None)

        return {
            '_type': 'url_transparent',
            'url': wistia_url,
            'ie_key': WistiaIE.ie_key(),
            'title': title,
        }


class TeachableCourseIE(TeachableBaseIE):
    _VALID_URL = r'''(?x)
                        (?:
                            %shttps?://(?P<site_t>[^/]+)|
                            https?://(?:www\.)?(?P<site>%s)
                        )
                        /(?:courses|p)/(?:enrolled/)?(?P<id>[^/?#&]+)
                    ''' % TeachableBaseIE._VALID_URL_SUB_TUPLE
    _TESTS = [{
        'url': 'http://upskillcourses.com/courses/essential-web-developer-course/',
        'info_dict': {
            'id': 'essential-web-developer-course',
            'title': 'The Essential Web Developer Course (Free)',
        },
        'playlist_count': 192,
    }, {
        'url': 'http://upskillcourses.com/courses/119763/',
        'only_matching': True,
    }, {
        'url': 'http://upskillcourses.com/courses/enrolled/119763',
        'only_matching': True,
    }, {
        'url': 'https://academy.gns3.com/courses/enrolled/423415',
        'only_matching': True,
    }, {
        'url': 'teachable:https://learn.vrdev.school/p/gear-vr-developer-mini',
        'only_matching': True,
    }, {
        'url': 'teachable:https://filmsimplified.com/p/davinci-resolve-15-crash-course',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if TeachableIE.suitable(url) else super(
            TeachableCourseIE, cls).suitable(url)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site = mobj.group('site') or mobj.group('site_t')
        course_id = mobj.group('id')

        self._login(site)

        prefixed = url.startswith(self._URL_PREFIX)
        if prefixed:
            prefix = self._URL_PREFIX
            url = url[len(prefix):]

        webpage = self._download_webpage(url, course_id)

        url_base = 'https://%s/' % site

        entries = []

        for mobj in re.finditer(
                r'(?s)(?P<li><li[^>]+class=(["\'])(?:(?!\2).)*?section-item[^>]+>.+?</li>)',
                webpage):
            li = mobj.group('li')
            if 'fa-youtube-play' not in li:
                continue
            lecture_url = self._search_regex(
                r'<a[^>]+href=(["\'])(?P<url>(?:(?!\1).)+)\1', li,
                'lecture url', default=None, group='url')
            if not lecture_url:
                continue
            lecture_id = self._search_regex(
                r'/lectures/(\d+)', lecture_url, 'lecture id', default=None)
            title = self._html_search_regex(
                r'<span[^>]+class=["\']lecture-name[^>]+>([^<]+)', li,
                'title', default=None)
            entry_url = urljoin(url_base, lecture_url)
            if prefixed:
                entry_url = self._URL_PREFIX + entry_url
            entries.append(
                self.url_result(
                    entry_url,
                    ie=TeachableIE.ie_key(), video_id=lecture_id,
                    video_title=clean_html(title)))

        course_title = self._html_search_regex(
            (r'(?s)<img[^>]+class=["\']course-image[^>]+>\s*<h\d>(.+?)</h',
             r'(?s)<h\d[^>]+class=["\']course-title[^>]+>(.+?)</h'),
            webpage, 'course title', fatal=False)

        return self.playlist_result(entries, course_id, course_title)
