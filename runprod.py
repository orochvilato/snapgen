# -*- coding: utf-8 -*-
from snapgen import app, app_path, memcache, fifo





if __name__ == "__main__":
    app.run(port=8888,processes=1)
