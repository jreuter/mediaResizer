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
import magic
import os
from PIL import Image


class MediaResizerException(Exception):
    """
    Excepton handling for the MediaResizer.
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class MediaResizer:
    _arguments = None
    _log_level = 'WARN'
    _default_size = 800, 600
    _folder = ''

    def __init__(self):
        """
        Gets command line arguments using docopt and sets logging level.
        """
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

    def resize_image(self, image, mime):
        """
        Resizes a single image.  Uses the mime type to determine what type of
        image to save and uses the file extension of the original in the new
        one.  This will need updated when the ability to output to a different
        format from the input is added.

        :param image: Full path of image to be processed.
        :param mime: Mime type of original image (same as new image for now).
        """
        try:
            im = Image.open(image)
            name, extension = os.path.splitext(image)
            sub_type = mime.split('/')[1]
            outfile = os.path.join(self._folder, name + '_resized' + extension)
            logging.error('creating file for %s.' % sub_type)
            im.thumbnail(self._default_size, Image.ANTIALIAS)
            im.save(outfile, sub_type.upper())
        except IOError:
            logging.error('Cannot create new image for %s.' % image)

    def main(self):
        """
        This does some sanity checks on the input.  Then loops through all the
        files in the directory, processing each one that has a mime type that
        is supported.
        """
        logging.info('Directory added: %s', self._arguments['<folder>'])
        self._folder = self._arguments['<folder>']

        # Make sure it's a folder before processing.
        if os.path.isfile(self._folder):
            logging.error('Program only handles folders.')
            exit(1)

        # Make sure it's not a dot folder (may be removed later).
        if os.path.basename(self._folder).startswith('.'):
            logging.info('Ignoring dot folders.')
            exit()

        # Get all files in the directory, but only files.
        files = [f for f in os.listdir(self._folder)
                 if os.path.isfile(os.path.join(self._folder, f))]

        # Loop through file list for processing.
        for file in files:
            # Get mime type (I hate that it's called magic).
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(os.path.join(self._folder, file))
            # If it's an image, pass to the image resizer.
            # TODO(jreuter): Make this smarter since we can't process all types
            # of images.
            if mime_type.startswith('image'):
                self.resize_image(os.path.join(self._folder, file), mime_type)


if __name__ == '__main__':
    MediaResizer().main()
