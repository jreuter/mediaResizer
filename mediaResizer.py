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
import pyexiv2
import subprocess


class MediaResizerException(Exception):
    """
    Exception handling for the MediaResizer.
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
            full_path = os.path.join(self._folder, image)
            im = Image.open(full_path)
            # TODO(jreuter): Split this to a function.
            metadata = pyexiv2.ImageMetadata(full_path)
            metadata.read()
            name, extension = os.path.splitext(image)
            sub_type = mime.split('/')[1]
            # TODO(jreuter): Store this in a variable to be re-used.
            size_string = str(self._default_size[0]) + \
                          'x' + str(self._default_size[1])
            new_folder = 'resized_' + size_string
            directory = os.path.join(self._folder, new_folder)
            if not os.path.exists(directory):
                os.makedirs(directory)
            outfile = os.path.join(directory,
                                   name + '_' + size_string + extension)
            logging.info('creating file for %s.' % outfile)
            im.thumbnail(self._default_size, Image.ANTIALIAS)
            im.save(outfile, sub_type.upper())
            # TODO(jreuter): Split this out to a function.
            outfile_metadata = pyexiv2.ImageMetadata(outfile)
            outfile_metadata.read()
            metadata.copy(outfile_metadata)
            outfile_metadata.write()
        except IOError:
            logging.error('Cannot create new image for %s.' % image)

    def convert_video(self, video, mime):
        """
        Converts one video using HandBrakeCLI.  This currently only works on
        linux since it builds a full path to the binary in /usr/bin/.

        :param video: Video file to convert.
        :param mime: MimeType string of file.
        """
        try:
            full_path = os.path.join(self._folder, video)
            name, extension = os.path.splitext(video)
            # TODO(jreuter): Store this in a variable to be re-used.
            size_string = str(self._default_size[0]) + \
                          'x' + str(self._default_size[1])
            new_folder = 'resized_' + size_string
            directory = os.path.join(self._folder, new_folder)
            destination_file = os.path.join(directory, name + '.m4v')
            if not os.path.exists(directory):
                os.makedirs(directory)
            handbrake_command = [
                os.path.join(os.path.sep, 'usr', 'bin', 'HandBrakeCLI'),
                '-i', full_path,
                '-o', destination_file
            ]
            logging.debug('cmd is %s' % ' '.join(handbrake_command))
            logging.info('Creating file %s.' % destination_file)
            handbrake = subprocess.Popen(
                handbrake_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            handbrake.wait()
            out, err = handbrake.communicate()
            if handbrake.returncode or err:
                logging.error('Error from Handbrake: %s' % err)
            logging.info('Done with video: %s.' % destination_file)
        except OSError as ex:
            logging.error('OS Error: %s.' % ex)
        except IOError:
            logging.error('Cannot create new video for %s.' % video)

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
            # TODO(jreuter): Can we pull mimetype from pyexiv2?
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(os.path.join(self._folder, file))
            # If it's an image, pass to the image resizer.
            # TODO(jreuter): Make this smarter since we can't process all types
            # of images.
            if mime_type.startswith('image'):
                self.resize_image(file, mime_type)
            else:
                self.convert_video(file, mime_type)


if __name__ == '__main__':
    MediaResizer().main()
