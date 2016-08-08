# -*- coding: utf-8 -*-

from staticpage import utils, gen


if __name__ == '__main__':
    utils.init_logger()
    gen.create_site(debug=False, use_reloader=True)
