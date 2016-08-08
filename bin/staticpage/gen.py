# -*- coding: utf-8 -*-

import logging
from multiprocessing import Process
import os
from os.path import dirname, realpath, join
import shutil
import signal
import sys

from staticjinja import make_site, Reloader
from webassets import Environment, Bundle
from webassets.ext.jinja2 import AssetsExtension
from webassets.script import CommandLineEnvironment

from .utils import mkdirp

log = logging.getLogger('webassets')


# HACK: 当 js/css 变化时, 强制重新渲染
def event_handler(self, event_type, src_path):
    filename = os.path.relpath(src_path, self.searchpath)
    if self.should_handle(event_type, src_path):
        print("%s %s" % (event_type, filename))
        if self.site.is_static(filename):
            files = self.site.get_dependencies(filename)
            self.site.copy_static(files)
            # js/css变化时, 强制重新渲染
            self.site.render_templates(self.site.templates)
        else:
            templates = self.site.get_dependencies(filename)
            self.site.render_templates(templates)


Reloader.event_handler = event_handler


PROJECT_ROOT_DIR = dirname(dirname(realpath(dirname(__file__))))

REL_SITE_SRC_DIR = 'src'
SITE_SRC_DIR = join(PROJECT_ROOT_DIR, 'src')
WEBASSETS_CACHE_DIR = join(PROJECT_ROOT_DIR, '.webassets-cache')
SITE_ASSET_SRC_DIR = join(PROJECT_ROOT_DIR, 'asset')
SITE_ASSET_URL_PREFIX = '/asset'

SITE_DIR = join(PROJECT_ROOT_DIR, 'public')
SITE_ASSET_DIR = join(SITE_SRC_DIR, 'asset')
REL_SITE_ASSET_DIR = 'asset'


def _init_dirs():
    mkdirp(WEBASSETS_CACHE_DIR)
    mkdirp(SITE_DIR)
    shutil.rmtree(SITE_ASSET_DIR)


def _init_webassets(debug=False):
    assets_env = Environment(directory=SITE_ASSET_DIR,
                             url=SITE_ASSET_URL_PREFIX,
                             cache=WEBASSETS_CACHE_DIR,
                             load_path=[SITE_ASSET_SRC_DIR])
    assets_env.debug = debug

    js = Bundle('js/*.js', filters='uglifyjs', output='js/app.js')
    css = Bundle('sass/*.scss', filters='scss,cssmin', output='css/app.css')

    assets_env.register('app_js', js)
    assets_env.register('app_css', css)

    cmd = CommandLineEnvironment(assets_env, log)

    p = Process(target=lambda: cmd.watch())

    def signal_handler(sig, frame):
        p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    p.start()

    return assets_env


def create_site(debug=False, use_reloader=False):
    _init_dirs()
    assets_env = _init_webassets(debug=debug)
    site = make_site(searchpath=SITE_SRC_DIR,
                     staticpaths=[REL_SITE_ASSET_DIR],
                     outpath=SITE_DIR,
                     extensions=[AssetsExtension])
    # HACK: staticjinja没有提供 jinja2.Environment 的引用,
    # 因此这里只能访问其私有属性进行设置
    site._env.assets_environment = assets_env
    site.render(use_reloader=use_reloader)
