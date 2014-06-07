#!/usr/bin/env python
# encoding: utf-8
# Copyright 2014 Jarrod Reuter

"""
Program to process images and videos to desired format, resolution, and size.

Usage:
    mediaResizer [options] <folder>
    mediaResizer -h | --help
    mediaResizer --version

Options:
    -h --help       Show this screen.
    --version       Show version.
    -q              Quiet the logging to only ERROR level.
    -v              Verbose output (INFO level).
    --debug         Very Verbose output (DEBUG level).
"""
from docopt import docopt
import logging
import os
from PIL import Image


class MediaResizerException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class MediaResizer:
    _arguments = None
    _log_level = 'WARN'
    _default_size = 800, 600

    def __init__(self):
        self._arguments = docopt(__doc__, version='0.1')
        self._set_logging_verbosity()

    def _set_logging_verbosity(self):
        """
        Sets the logging level based on arguments passed in the cli.
        """
        if self._arguments['-v']:
            self._log_level = logging.INFO
        if self._arguments['--debug']:
            self._log_level = logging.DEBUG
        if self._arguments['-q']:
            self._log_level = logging.ERROR
        logging.basicConfig(level=self._log_level,
                            format='%(asctime)s %(message)s')

    def main(self):
        logging.info('Directory added: %s', self._arguments['<folder>'])

        if os.path.basename(self._arguments['<folder>']).startswith('.'):
            logging.info('Ignoring dot files.')
            exit()

        # Testing with one file instead of foler for now.
        img_filename = self._arguments['<folder>']
        try:
            im = Image.open(img_filename)
            # im.show()
            outfile = os.path.splitext(img_filename)[0] + '_resized.jpg'
            im.thumbnail(self._default_size, Image.ANTIALIAS)
            im.save(outfile, 'JPEG')
        except IOError:
            logging.error('Cannot create new image for %s.' % img_filename)


if __name__ == '__main__':
    MediaResizer().main()
