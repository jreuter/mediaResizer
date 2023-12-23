#!/usr/bin/env python
# encoding: utf-8

"""
Program to process images to webp format.

Usage:
    webpConverter [options] <folder>
    webpConverter -h | --help
    webpConverter --version

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
import subprocess
from multiprocessing import Pool


def unwrap_self(arg, **kwarg):
    return WebPConverter.do_converstion(*arg, **kwarg)


class WebPConverterException(Exception):
    """
    Exception handling for the MediaResizer.
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class WebPConverter:
    _arguments = None
    _log_level = 'WARN'
    _default_size = 1920, 1080
    _folder = ''
    _thread_list = []

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

    # def _image(self, image, mime):

    def do_converstion(self, medium):
        print "Starting process for medium: %s." % medium
        # Get mime type (I hate that it's called magic).
        # TODO(jreuter): Can we pull mimetype from pyexiv2?
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(os.path.join(self._folder, medium))
        # If it's an image, pass to the image resizer.
        # TODO(jreuter): Make this smarter since we can't process all types
        # of images.

        if mime_type.startswith('image'):
            try:
                name, extension = os.path.splitext(medium)
                full_path = os.path.join(self._folder, medium)
                outfile = os.path.join(self._folder,
                                       name + '.webp')
                webp_command = [
                    'cwebp',
                    '-q', '80',
                    full_path,
                    '-o', outfile
                ]
                webp = subprocess.Popen(
                    webp_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                out, err = webp.communicate()
                if webp.returncode or err:
                    logging.error('Error from cwebp %s.' % err)
                    return
                logging.info('Done with webp: %s.' % outfile)
            except OSError as ex:
                logging.error('OS Error: %s.' % ex)
            except IOError:
                logging.error('Cannot create new webp for %s.' % medium)
            # self.resize_image(medium, mime_type)
        # else:
        #     # TODO(jreuter): Queue videos and convert later.
        #     self.convert_video(medium, mime_type)
        print "Done processing medium: %s." % medium

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
        pool = Pool()
        results = pool.map(unwrap_self, zip([self] * len(files), files))
        print "Finished processing media."


if __name__ == '__main__':
    WebPConverter().main()
