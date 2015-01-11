# Random trailer player
#
# Author - kzeleny
# Version - 1.1.17
# Compatibility - Frodo/Gothum
#

import xbmc
import xbmcvfs
import xbmcgui
from urllib import quote_plus, unquote_plus
import datetime
import urllib
import urllib2
import re
import sys
import os
import random
import json
import time
import xbmcaddon
import xml.dom.minidom
from xml.dom.minidom import Node

addon = xbmcaddon.Addon()
# number_trailers =  0
# volume = int(addon.getSetting("volume"))
# quality = addon.getSetting("quality")
# quality = ["480p", "720p", "1080p"][int(quality)]
# currentVolume = xbmc.getInfoLabel("Player.Volume")
# currentVolume = int((float(currentVolume.split(" ")[0])+60.0)/60.0*100.0)
# trailer_type = int(addon.getSetting('trailer_type'))
# hide_info = addon.getSetting('hide_info')
# hide_title = addon.getSetting('hide_title')
# trailers_path = addon.getSetting('path')
addon_path = addon.getAddonInfo('path')
# hide_watched = addon.getSetting('hide_watched')
# watched_days = addon.getSetting('watched_days')
# resources_path = xbmc.translatePath( os.path.join( addon_path, 'resources' ) ).decode('utf-8')
# media_path = xbmc.translatePath( os.path.join( resources_path, 'media' ) ).decode('utf-8')
# selectedGenre =''
# exit_requested = False
# movie_file = ''
#
# if len(sys.argv) == 2:
#     do_genre ='false'
#
# trailer=''
# info=''
# do_timeout = False
played = []

def getTitleFont():
    title_font = 'font13'
    multiplier = 1
    skin_dir = xbmc.translatePath("special://skin/")
    list_dir = os.listdir(skin_dir)
    fonts = []
    fontxml_path = ''
    font_xml = ''
    for item in list_dir:
        item = os.path.join( skin_dir, item )
        if os.path.isdir( item ):
            font_xml = os.path.join( item, "Font.xml" )
        if os.path.exists( font_xml ):
            fontxml_path=font_xml
            break
    dom =  xml.dom.minidom.parse(fontxml_path)
    fontlist=dom.getElementsByTagName('font')
    for font in fontlist:
        name = font.getElementsByTagName('name')[0].childNodes[0].nodeValue
        size = font.getElementsByTagName('size')[0].childNodes[0].nodeValue
        fonts.append({'name':name,'size':float(size)})
    fonts =sorted(fonts, key=lambda k: k['size'])
    for f in fonts:
        if f['name']=='font13':
            multiplier=f['size'] / 20
            break
    for f in fonts:
        if f['size'] >= 38 * multiplier:
            title_font=f['name']
            break
    return title_font

def getSteamTrailers():
    tmdbTrailers=[]

    url = 'http://api.steampowered.com/ISteamApps/GetAppList/v0002/'
    req = urllib2.Request(url)

    infostring = urllib2.urlopen(req).read()
    jsonAppData = json.loads(infostring)
    appDataArray = jsonAppData['applist']['apps']
    random.shuffle(appDataArray)

    for i in range(0, len(appDataArray)):
        appId = appDataArray[i]['appid']
        name = appDataArray[i]['name']

        dict={'trailer':'steam','id': appId,'source':'steam','title':name}
        tmdbTrailers.append(dict)

    return tmdbTrailers

def getSteamTrailer(appId):
    data = {}
    data['appids'] = appId
    data['filters'] = 'movies'
    url_values = urllib.urlencode(data)
    url = 'http://store.steampowered.com/api/appdetails'
    full_url = url + '?' + url_values
    req = urllib2.Request(full_url)
    infostring = urllib2.urlopen(req).read()
    infostring = json.loads(infostring)
    gameEntry = infostring[str(appId)]
    if 'data' in gameEntry:
        gameData = gameEntry['data']
        if 'movies' in gameData:
            movieData = gameData['movies']
            random.shuffle(movieData)
            movie = movieData[0]
            if 'webm' in movie:
                name = movie['name']
                url = movie['webm']['max']
                dict={'trailer':url,'id': appId,'source':'steam','title':name,'year':'20XX'}
                return dict

    print 'No movies for game with appid ' + str(appId)
    return ''


class blankWindow(xbmcgui.WindowXML):
    def onInit(self):
        pass
        
class trailerWindow(xbmcgui.WindowXMLDialog):

    def onInit(self):
        windowstring = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"GUI.GetProperties","params":{"properties":["currentwindow"]},"id":1}')
        windowstring=json.loads(windowstring)
        xbmc.log('Trailer_Window_id = ' + str(windowstring['result']['currentwindow']['id']))
        global played
        global SelectedGene
        global trailer
        global info
        global do_timeout
        global NUMBER_TRAILERS
        global trailercountF
        global source
        random.shuffle(trailers)
        trailercount=0
        trailer=random.choice(trailers)
        while trailer['title'] in played:
            trailer=random.choice(trailers)
            trailercount=trailercount+1
            if trailercount == len(trailers):
                played=[]
        if trailer['trailer']=='steam':
            newtrailer=getSteamTrailer(trailer['id'])
            print 'NEWTRAILER' + str(newtrailer) + 'NEWTRAILER'
            if newtrailer == '' or newtrailer['trailer'] == '':
                trailer['trailer']=''
                played.append(trailer['title'])
                self.close()
            trailer['trailer'] = newtrailer['trailer']
            print 'PROCEEDING' + trailer['trailer'] + 'PROCEEDING'
        played.append(trailer['title'])
        source=trailer['source']
        lastPlay = True

        url = trailer['trailer'].encode('ascii', 'ignore')

        xbmc.log(str(trailer))

        if trailer["trailer"] != '' and lastPlay:
            NUMBER_TRAILERS = NUMBER_TRAILERS -1
            xbmc.Player().play(url)
            NUMBER_TRAILERS = NUMBER_TRAILERS -1
            self.getControl(30011).setLabel('[B]' + trailer['title'] + ' - ' + trailer['source'] + '[/B]')
            self.getControl(30011).setVisible(False)

            while xbmc.Player().isPlaying():                
                xbmc.sleep(250)
        self.close()
        
    def onAction(self, action):
        ACTION_PREVIOUS_MENU = 10
        ACTION_BACK = 92
        ACTION_ENTER = 7
        ACTION_I = 11
        ACTION_LEFT = 1
        ACTION_RIGHT = 2
        ACTION_UP = 3
        ACTION_TAB = 18
        ACTION_M = 122

        global exit_requested
        global movie_file
        global source
        global trailer
        movie_file=''
        xbmc.log(str(action.getId()))

        if action == ACTION_PREVIOUS_MENU or action == ACTION_LEFT or action == ACTION_BACK:
            xbmc.Player().stop()
            exit_requested = True
            self.close()

        if action == ACTION_RIGHT or action == ACTION_TAB:
            xbmc.Player().stop()
            
        if action == ACTION_ENTER:
            exit_requested = True
            xbmc.Player().stop()
            movie_file = trailer["file"]
            self.getControl(30011).setVisible(False)
            self.close()
            
        if action == ACTION_M:
            self.getControl(30011).setVisible(True)
            xbmc.sleep(2000)
            self.getControl(30011).setVisible(False)
        
        if action == ACTION_I or action == ACTION_UP:
            if source != 'folder':
                self.getControl(30011).setVisible(False)
                w=infoWindow('script-DialogVideoInfo.xml',addon_path,'default')
                xbmc.Player().pause()
                w.doModal()
                xbmc.Player().pause()
            self.getControl(30011).setVisible(False)
                              
class infoWindow(xbmcgui.WindowXMLDialog):
    def onInit(self):
        source = trailer['source']
        title_font=getTitleFont()
        title_string =trailer["title"] # + ' - ' + trailer['source'] + ' ' + trailer['type'] + ' - ' + str(trailer["year"])
        title=xbmcgui.ControlLabel(10,40,800,40,title_string,title_font)
        title=self.addControl(title)
        title=self.getControl(3001)
        title.setAnimations([('windowclose', 'effect=fade end=0 time=1000')])          
        if do_timeout:
            xbmc.sleep(6000)
            self.close()
        
    def onAction(self, action):
        ACTION_PREVIOUS_MENU = 10
        ACTION_BACK = 92
        ACTION_ENTER = 7
        ACTION_I = 11
        ACTION_LEFT = 1
        ACTION_RIGHT = 2
        ACTION_UP = 3
        ACTION_DOWN = 4
        ACTION_TAB = 18
        ACTION_Q = 34
        
        global do_timeout
        global exit_requested
        global trailer
        global movie_file
        movie_file=''
        
        if action == ACTION_PREVIOUS_MENU or action == ACTION_LEFT or action == ACTION_BACK:
            do_timeout=False
            xbmc.Player().stop()
            exit_requested=True
            self.close()

        if action == ACTION_I or action == ACTION_DOWN:
            self.close()
            
        if action == ACTION_RIGHT or action == ACTION_TAB:
            xbmc.Player().stop()
            self.close()

        if action == ACTION_ENTER:
            movie_file = trailer["file"]
            xbmc.Player().stop()
            exit_requested=True
            self.close()


def play_trailers():
    global exit_requested
    global movie_file
    global NUMBER_TRAILERS
    global trailercount
    movie_file = ''
    exit_requested = False
    DO_CURTIANS = addon.getSetting('do_animation')
    DO_EXIT = addon.getSetting('do_exit')
    NUMBER_TRAILERS =  int(addon.getSetting('number_trailers'))
    GROUP_TRAILERS = False
    if addon.getSetting('group_trailers')=='true':GROUP_TRAILERS = True
    GROUP_NUMBER = int(addon.getSetting('group_number'))
    GROUP_COUNT=GROUP_NUMBER
    GROUP_DELAY = (int(addon.getSetting('group_delay')) * 60) * 1000
    trailercount = 0
    while not exit_requested:
        if NUMBER_TRAILERS == 0:
            while not exit_requested and not xbmc.abortRequested:
                if GROUP_TRAILERS:
                    GROUP_COUNT=GROUP_COUNT - 1
                mytrailerWindow = trailerWindow('script-trailerwindow.xml', addon_path,'default',)
                mytrailerWindow.doModal()
                del mytrailerWindow
                if GROUP_TRAILERS and GROUP_COUNT==0:
                    GROUP_COUNT=GROUP_NUMBER
                    i = GROUP_DELAY
                    while i > 0 and not exit_requested and not xbmc.abortRequested:
                        xbmc.sleep(500)
                        i=i-500                      
        else:
            while NUMBER_TRAILERS > 0:
                if GROUP_TRAILERS:
                    GROUP_COUNT=GROUP_COUNT - 1
                mytrailerWindow = trailerWindow('script-trailerwindow.xml', addon_path,'default',)
                mytrailerWindow.doModal()
                del mytrailerWindow
                if GROUP_TRAILERS and GROUP_COUNT==0:
                    GROUP_COUNT=GROUP_NUMBER
                    i = GROUP_DELAY
                    while i > 0 and not exit_requested and not xbmc.abortRequested:
                        xbmc.sleep(500)
                        i=i-500  
                if exit_requested:
                    break
        if not exit_requested:
            if DO_CURTIANS == 'true':
                xbmc.Player().play(close_curtain_path)
                while xbmc.Player().isPlaying():
                    xbmc.sleep(250)
        exit_requested=True

if not xbmc.Player().isPlaying():
    bs = blankWindow('script-BlankWindow.xml', addon_path,'default',)
    bs.show()

    trailers = []
    trailerNumber = 0

    dp=xbmcgui.DialogProgress()
    dp.create('Random Game Trailers','','','Loading Trailers')

    steamTrailers = getSteamTrailers()
    for trailer in steamTrailers:
        trailers.append(trailer)
    exit_requested = False
    if dp.iscanceled():
        exit_requested = True
    dp.close()

    if len(trailers) > 0 and not exit_requested:
        play_trailers()
    del bs

else:
    xbmc.log('Random Game Trailers: ' + 'Exiting Random Game Trailers Screen Saver Something is playing!!!!!!')
