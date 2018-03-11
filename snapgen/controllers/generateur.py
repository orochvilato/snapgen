# -*- coding: utf-8 -*-
from genvisu import app,memcache

from selenium import webdriver
from selenium.webdriver.chrome import service

import StringIO
import datetime
import time
import re
import tempfile
import os
from io import BytesIO


def savepage(url,size,key):
    import time
    from selenium import webdriver


    wait = 5
    export_pos = memcache.get('gv_export_pos') or 0
    memcache.set('gv_export_pos',export_pos+1,1200)
    from math import log10
    while get_processes_count('chrome')>2:
        wait += 1
        time.sleep(0.5)
        memcache.set(key,{'etat':u"Position file d'attente : %d" % export_pos,'avancement':int(7*log10(wait))})

    memcache.set('gv_export_pos',export_pos,1200)
    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/google-chrome'
    options.add_argument('headless')
    options.add_argument('window-size=%sx%s' % (size[0],size[1]+100))
    cdservice = service.Service('/usr/bin/chromedriver')
    memcache.set(key,{'etat':u'Génération du visuel','avancement':20})
    cdservice.start()
    driver = webdriver.Chrome(chrome_options=options)
    memcache.set(key,{'etat':u'Génération du visuel','avancement':30})

    driver.get(url);
    memcache.set(key,{'etat':u'Génération du visuel','avancement':40})
    #time.sleep(5) # Let the user actually see something!

    for i in range(6):
        time.sleep(3)
        memcache.set(key,{'etat':u'Génération du visuel','avancement':60+i*5})

    im = Image.open(StringIO.StringIO(driver.get_screenshot_as_png()))
    im2 = im.crop((0,0,size[0],size[1]))
    driver.quit()
    cdservice.stop()
    output = StringIO.StringIO()
    im2.save(output,'PNG')
    memcache.set(key,{'etat':u'Génération du visuel','avancement':100})

    return output.getvalue()
