# -*- coding: utf-8 -*-
from snapgen import app, app_path, memcache, fifo
from snapgen.tools import image_response
from flask import request
from werkzeug.utils import secure_filename
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome import service
from PIL import Image,ImageChops,ImageFont,ImageDraw
from io import BytesIO
import time
from stegano import lsbset
from stegano.lsbset import generators
from threading import Thread

q = Queue()

nbworkers = 2

states = {}

keyqueue = []


def getSnapshot(url,width,height,name,key,visuel,watermark):
    from selenium import webdriver
    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/google-chrome'
    options.add_argument('headless')

    options.add_argument('window-size=%dx%d' % (width,height+100))
    cdservice = service.Service('/usr/bin/chromedriver')
    states[key] = {'etat':u'Génération du visuel','avancement':20}
    cdservice.start()
    driver = webdriver.Chrome(chrome_options=options)
    states[key] = {'etat':u'Génération du visuel','avancement':30}

    driver.get(url);
    states[key] = {'etat':u'Génération du visuel','avancement':40}


    for i in range(6):
        time.sleep(0.5)
        states[key] = {'etat':u'Génération du visuel','avancement':60+i*5,'url':url}

    im = Image.open(BytesIO(driver.get_screenshot_as_png()))
    im2 = im.crop((0,0,width,height))
    driver.quit()
    cdservice.stop()
    output = BytesIO()
    import json
    data = json.loads(watermark)
    if data['visuel'] in ['urgdem','urgsoc','eurque','paxint','prohum','urgeco']:
        im2 = add_corners(im2,30)

    im2.save(output,'PNG')

    # Watermark / stegano

    import json
    output.seek(0)
    secret_image = lsbset.hide(output, watermark, generators.eratosthenes())
    output_final = BytesIO()
    secret_image.save(output_final,'PNG')

    states[key] = {'etat':u'Génération du visuel','avancement':100}

    return output.getvalue()
    return output_final.getvalue()


def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    print(w,h)
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im




def worker():
    while True:
        item = q.get()
        retries = 6
        while retries>0:
            try:
                snapshot = getSnapshot(**item)
                memcache.set(item['key']+'_image',{'image':snapshot,'name':item['name']},60)
                retries = -1
            except:
                retries -= 1

        if retries>=0:
            states[item['key']] = {'etat':u'Erreur','avancement':-1}
        keyqueue.remove(item['key'])
        q.task_done()



for i in range(nbworkers):
    workthread = Thread(target=worker)
    workthread.daemon = True
    workthread.start()

@app.route('/retrieve_snapshot')
def retrieve_image():
    key = request.args.get('key')
    if not key:
        return "Nope"
    data = memcache.get(key+'_image')
    if not data:
        return "Nope"
    return image_response('png',data['image'],filename=data['name'])

@app.route('/status')
def status():

    key = request.args.get('key')
    if not key:
        data = {'etat':'Erreur','avancement':-1}
    else:
        data = states.get(key,None)

        if data and key in keyqueue:
            data.update(position=keyqueue.index(key))

    if not data:
        data = {'etat':'Erreur','avancement':-1}
    import json
    return json.dumps(data)

@app.route('/prepare',methods=['POST'])
def prepare():
    data = request.form

    import uuid
    key = str(uuid.uuid4())

    item = {
        'url':request.form.get('url'),
        'name':request.form.get('name'),
        'width':int(request.form.get('width') or 1024),
        'height':int(request.form.get('height') or 1024), 'visuel':request.form.get('visuel'),'key':key,'watermark':request.form.get('watermark')}

    states[key] = {'etat':'En attente','avancement':0,'url':item['url']}
    keyqueue.append(key)
    q.put(item)
    return key

ALLOWED_EXTENSIONS = ['png']
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/checkfile', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            fic = BytesIO()
            file.save(fic)
            fic.seek(0)
            return lsbset.reveal(fic, generators.eratosthenes())


    return '''
    <!doctype html>
    <title>Contrôle Image</title>
    <h1>Contrôle image</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''
