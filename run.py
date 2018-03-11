# -*- coding: utf-8 -*-
from snapgen import app, app_path, memcache, fifo





if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8888,debug=True,processes=1)
