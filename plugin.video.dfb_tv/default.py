﻿#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 2.X
	from urllib2 import build_opener, HTTPCookieProcessor, Request, urlopen  # Python 2.X
	from cookielib import LWPCookieJar  # Python 2.X
	from urlparse import urljoin, urlparse, urlunparse  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode, urljoin, urlparse, urlunparse  # Python 3+
	from urllib.request import build_opener, HTTPCookieProcessor, Request, urlopen  # Python 3+
	from http.cookiejar import LWPCookieJar  # Python 3+
import xbmcvfs
import shutil
import socket
import time
import datetime
import io
import gzip


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
is_xbox = xbmc.getCondVisibility("System.Platform.xbox")
if is_xbox: HD = False
else: HD = addon.getSetting("maxVideoQuality") == "1"

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

def py2_enc(s, encoding='utf-8'):
    if PY2 and isinstance(s, unicode):
        s = s.encode(encoding)
    return s

def py2_uni(s, encoding='utf-8'):
    if PY2 and isinstance(s, str):
        s = unicode(s, encoding)
    return s

def py3_dec(d, encoding='utf-8'):
    if PY3 and isinstance(d, bytes):
        d = d.decode(encoding)
    return d

def translation(id):
    LANGUAGE = addon.getLocalizedString(id)
    LANGUAGE = py2_enc(LANGUAGE)
    return LANGUAGE

def failing(content):
    log(content, xbmc.LOGERROR)

def debug(content):
    log(content, xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
    msg = py2_enc(msg)
    xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+msg, level)

def getUrl(url, header=None, referer=None):
    req = Request(url)
    try:
        if header:
            req.add_header = header
        else:
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0')
            req.add_header('Accept-Encoding','gzip, deflate')
        if referer:
            req.add_header('Referer', referer)
        response = urlopen(req, timeout=30)
        if response.info().get('Content-Encoding') == 'gzip':
            link = py3_dec(gzip.GzipFile(fileobj=io.BytesIO(response.read())).read())
        else:
            link = py3_dec(response.read())
    except Exception as e:
        failure = str(e)
        if hasattr(e, 'code'):
            failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
        elif hasattr(e, 'reason'):
            failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
        link = ""
        return sys.exit(0)
    response.close()
    return link

def index():
    add_category(title = translation(30601), mode = 'list-videos')
    add_category(title = translation(30602), mode = 'category-men',)
    add_category(title = translation(30603), mode = 'category-women')
    add_category(title = translation(30604), mode = 'list-videos', categories = 'Wettbewerbe+International')
    add_category(title = translation(30605), mode = 'list-videos', categories = 'Amateurfußball')
    add_category(title = translation(30606), mode = 'list-videos', categories = 'Fan+Club')
    add_category(title = translation(30607), mode = 'list-videos', categories = 'English+Videos')
    add_category(title = translation(30608), mode = 'list-livestreams')
    add_category(title = translation(30609), mode = 'search')
    xbmcplugin.endOfDirectory(pluginhandle)

def get_last_page(total_results):
    if not total_results: return 0
    if total_results % 10 == 0: return total_results // 10
    return total_results // 10 + 1

def clean_text(text):
    return text.replace('\n', '').replace('\t', '').replace('&amp;', '&').replace('   ', '').replace('  ', ' ').replace('\\"', '"').replace('\\u0026', '&').replace('\\t', '').replace(': :', ':').strip()

def list_all_livestreams(live_url = 'https://tv.dfb.de/static/livestreams/'):
    try:
        html = getUrl(live_url)
        regex_videos = '<div class="video-teaser.*?<img src=".*?/images/(.+?)_.*?subline">(.+?)</.*?-headline">(.+?)</'
        videos = re.findall(regex_videos, html, re.DOTALL)
    except: return False
    item_added = False
    for video in videos:
        try:
            video_id = video[0]
            subline = clean_text(video[1])
            title = clean_text(video[2])
            if HD: thumb = 'https://search.dfb.de/proxy/large_hires?url=https://tv.dfb.de/images/' + video_id + '_1360x760.jpg'
            else: thumb = 'https://search.dfb.de/proxy/medium_hires?url=https://tv.dfb.de/images/' + video_id + '_1360x760.jpg'
            relevance = subline[:subline.find('//')].strip()
            try:
                datetime_object = datetime.datetime.strptime(relevance, '%d.%m.%Y - %H:%M')
            except TypeError:
                try:
                    datetime_object = datetime.datetime(*(time.strptime(relevance, '%d.%m.%Y - %H:%M')[0:6]))
                except: datetime_object = ""
            if datetime_object != "":
                actualTIME = datetime_object.strftime("%H:%M")
                if 'jetzt live' in title.lower():
                    add_video('[COLOR lime]'+title+'[/COLOR]  (ab '+actualTIME+')', video_id, thumb, 'play-livestream', title + '\n' + subline)
                else:
                    add_video(relevance+' • '+title, video_id, thumb, 'play-livestream', title + '\n' + subline)
                item_added = True
            else:
                if 'jetzt live' in title.lower():
                    add_video('[COLOR lime]'+title+'[/COLOR]  ('+relevance+')', video_id, thumb, 'play-livestream', title + '\n' + subline)
                else:
                    add_video(relevance+' • '+title, video_id, thumb, 'play-livestream', title + '\n' + subline)
                item_added = True
        except: continue
    if not item_added: return warning(translation(30523))
    xbmcplugin.endOfDirectory(pluginhandle)
    return True

def get_search_string():
    keyboard = xbmc.Keyboard('', translation(30609))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        return keyboard.getText().replace(" ", "+")
    return False

def list_all_videos(search_string = '', categories = '', current_page = 1, last_page = 0, meta = ''):
    json_url = 'http://search.dfb.de/search/videos.json?'
    if search_string: json_url += 'q=' + search_string + '&'
    if categories: json_url += 'categories=' + categories + '&'
    if meta: json_url += 'meta_attribute_ids' + meta + '&'
    json_url += 'page=' + str(current_page)
    try:
        json = getUrl(json_url)
        if HD: regex_video_info = '"guid":.*?"video-(.+?)","title":"(.+?)",.*?"medium_hires":"(.+?)",.*?"pub_date":"(.+?)"'
        else: regex_video_info = '"guid":.*?"video-(.+?)","title":"(.+?)",.*?"image_url":"(.+?)",.*?"pub_date":"(.+?)"'
        videos = re.findall(regex_video_info, json, re.DOTALL)
    except: return False
    item_added = False
    for video in videos:
        try:
            video_id = video[0]
            title = clean_text(video[1])
            if HD: thumb = video[2].replace('medium_hires', 'large_hires')
            else: thumb = video[2].replace('medium?', 'medium_hires?')
            date = video[3].strip()
            add_video(date + ' - ' + title, video_id, thumb, 'play-video')
            item_added = True
        except: continue
    if not item_added: return warning(translation(30523))
    if not last_page: 
        regex_total = '"total":(.+?),'
        try: last_page = get_last_page(int(re.findall(regex_total, json)[0]))
        except: last_page = current_page
    if current_page < last_page:
        add_category((translation(30610).format(current_page+1)), 'list-videos', '', current_page + 1, last_page, search_string, categories, meta)
    xbmcplugin.endOfDirectory(pluginhandle)
    return True

def add_video(title, video_id, thumb, mode, desc = ''):
    link = sys.argv[0] + "?id=" + video_id + "&title=" + quote_plus(title) + "&thumb=" + quote_plus(thumb) + "&mode=" + str(mode)
    liz = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=thumb)
    liz.setInfo(type="Video", infoLabels={"Title": title, "Plot": desc})
    if thumb != icon:
        liz.setArt({'fanart': thumb})
    else:
        liz.setArt({'fanart': defaultFanart})
    liz.setProperty('IsPlayable', 'true')
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=link, listitem=liz)

def add_category(title, mode, thumb = '', current_page = 1, last_page = 0, search_string = '', categories = '', meta = ''):
    link = sys.argv[0] + "?current_page=" + str(current_page) + "&last_page=" + str(last_page) + "&thumb=" + quote_plus(thumb) + "&mode=" + str(mode)
    if search_string: link += '&search_string=' + quote_plus(search_string)
    if categories: link += '&categories=' + quote_plus(categories)
    if meta: link += '&meta=' + quote_plus(meta)
    liz = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=thumb)
    liz.setInfo(type="Video", infoLabels={"Title": title})
    if thumb != "" and thumb != icon:
        liz.setArt({'fanart': thumb})
    else:
        liz.setArt({'fanart': defaultFanart})
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=link, listitem=liz, isFolder=True)

def play_video(title, stream, thumb):
    log("(play_video) streamURL : "+stream)
    listitem = xbmcgui.ListItem(path=stream)
    listitem.setInfo(type="Video", infoLabels={'Title': title})
    listitem.setArt({'thumb': thumb, 'fanart': thumb})
    listitem.setMimeType('application/vnd.apple.mpegurl')
    listitem.setContentLookup(False)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def get_stream_url(video_id):
    token_url = ""
    # https://tv.dfb.de/server/streamAccess.php?videoId=22862&target=17&partner=2180&label=web_dfbtv&area=testarea&format=iphone
    xml_url = 'https://tv.dfb.de/server/hd_video.php?play=' + video_id
    try:
        xml_data = getUrl(xml_url)
        if '<live>true</live>' in xml_data:
            if not ('<islive>true</islive>' in xml_data): return False
        regex_url = '<url>(.+?)</url>'
        xml_url_video = clean_text(re.findall(regex_url, xml_data, re.DOTALL)[0]).split('?')[0] + '?format=iphone'
        xml_url_video = 'http:' + xml_url_video.strip()
        xml_data_video = getUrl(xml_url_video)
        regex_url_video = 'url="(.+?)"'
        video_url = re.findall(regex_url_video, xml_data_video, re.DOTALL)[0]
        try:
            regex_auth_video = 'token auth="(.+?)"'
            token_url = re.findall(regex_auth_video, xml_data_video, re.DOTALL)[0]
        except: pass
    except: return False
    if '/dfb_live' in video_url and video_url.endswith('.m3u8') and token_url != "":
        complete_url = video_url+"?hdnea="+token_url
        return complete_url
    elif '/dfb_live' in video_url and video_url.endswith('.m3u8') and token_url == "":
        return False
    base_url = video_url[:video_url.find('_,')+2]
    if token_url != "":
        if not ',1200,' in video_url:
            if not ',800,' in video_url:
                if not ',500,' in video_url:
                    if not ',300,' in video_url: return False
                    return base_url + '300,.mp4.csmil/index_0_av.m3u8?hdnea='+token_url
                return base_url + '500,.mp4.csmil/index_0_av.m3u8?hdnea='+token_url
            return base_url + '800,.mp4.csmil/index_0_av.m3u8?hdnea='+token_url
        if HD: return base_url + '1200,.mp4.csmil/index_0_av.m3u8?hdnea='+token_url
        return base_url + '800,.mp4.csmil/index_0_av.m3u8?hdnea='+token_url
    else:
        if not ',1200,' in video_url:
            if not ',800,' in video_url:
                if not ',500,' in video_url:
                    if not ',300,' in video_url: return False
                    return base_url + '300,.mp4.csmil/index_0_av.m3u8'
                return base_url + '500,.mp4.csmil/index_0_av.m3u8'
            return base_url + '800,.mp4.csmil/index_0_av.m3u8'
        if HD: return base_url + '1200,.mp4.csmil/index_0_av.m3u8'
        return base_url + '800,.mp4.csmil/index_0_av.m3u8'

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def warning(text, title = 'DFB TV :', showTime = 8000):
    xbmcgui.Dialog().notification(title, text, icon, int(showTime))

params = parameters_string_to_dict(sys.argv[2])
mode = unquote_plus(params.get('mode', ''))
id = unquote_plus(params.get('id', ''))
title = unquote_plus(params.get('title', ''))
thumb = unquote_plus(params.get('thumb', ''))
c_page = unquote_plus(params.get('current_page', ''))
l_page = unquote_plus(params.get('last_page', ''))
search_st = unquote_plus(params.get('search_string', ''))
cat = unquote_plus(params.get('categories', ''))
meta_ids = unquote_plus(params.get('meta', ''))
referer = unquote_plus(params.get('referer', ''))

if mode == 'list-livestreams':
    if not list_all_livestreams(): warning(translation(30524))
elif mode == 'play-livestream':
    stream_url = get_stream_url(id)
    if stream_url: play_video(title, stream_url, thumb)
    else: warning(translation(30525))
elif mode == 'play-video':
    stream_url = get_stream_url(id)
    if stream_url: play_video(title, stream_url, thumb)
    else: warning(translation(30526))
elif mode == 'search':
    search_s = get_search_string()
    if search_s: list_all_videos(search_string = search_s)
elif mode == 'category-men':
    add_category(title = translation(30611), mode = 'list-videos', categories = 'Männer')
    add_category(title = translation(30612), mode = 'list-videos', categories = 'Die+Mannschaft')
    add_category(title = translation(30613), mode = 'list-videos', categories = 'Bundesliga')
    add_category(title = translation(30614), mode = 'list-videos', categories = 'DFB-Pokal')
    add_category(title = translation(30615), mode = 'list-videos', categories = 'U+21-Männer')
    add_category(title = translation(30616), mode = 'list-videos', categories = 'U20-Männer')
    add_category(title = translation(30617), mode = 'list-videos', search_string = 'junioren')
    xbmcplugin.endOfDirectory(pluginhandle)
elif mode == 'category-women':
    add_category(title = translation(30611), mode = 'list-videos', categories = 'Frauen')
    add_category(title = translation(30618), mode = 'list-videos', categories = 'Frauen+Nationalmannschaft')
    add_category(title = translation(30619), mode = 'list-videos', categories = 'Allianz+Frauen-Bundesliga')
    add_category(title = translation(30620), mode = 'list-videos', categories = 'DFB-Pokal+der+Frauen')
    add_category(title = translation(30621), mode = 'list-videos', search_string = 'juniorinnen')
    xbmcplugin.endOfDirectory(pluginhandle)
elif mode == 'list-videos':
    if not list_all_videos(search_st, cat, int(c_page), int(l_page), meta_ids): warning(translation(30527))
else:
    index()