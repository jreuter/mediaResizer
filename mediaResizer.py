#!/usr/bin/env python3
# encoding: utf-8
# Copyright 2014-2015 Jarrod Reuter

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
import psutil
from PIL import Image
import gi
gi.require_version('GExiv2', '0.10')
from gi.repository.GExiv2 import Metadata
import subprocess
from multiprocessing import Pool, cpu_count


def limit_cpu():
    "is called at every process start to lower the process priority."
    p = psutil.Process(os.getpid())
    # set to lowest priority, this is windows only, on Unix use ps.nice(19)
    # p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    p.nice(19)


def unwrap_self_photos(arg, **kwarg):
    return MediaResizer.resize_image(*arg, **kwarg)


def unwrap_self_videos(arg, **kwarg):
    return MediaResizer.convert_video(*arg, **kwarg)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


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
    _default_size = 1920, 1080
    _size_string = ''
    _folder = ''
    _new_folder = ''
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

    def resize_image(self, photo):
        """
        Resizes a single image.  Uses the mime type to determine what type of
        image to save and uses the file extension of the original in the new
        one.  This will need updated when the ability to output to a different
        format from the input is added.

        :param image: Full path of image to be processed.
        :param mime: Mime type of original image (same as new image for now).
        """
        try:
            print(f"{bcolors.OKCYAN}Processing file {photo['input']} now.{bcolors.ENDC}")
            # full_path = photo.full_path
            im = Image.open(photo['full_path'])
            # TODO(jreuter): Split this to a function.
            # metadata = pyexiv2.ImageMetadata(full_path)
            metadata = Metadata(photo['full_path'])
            # stinfo = os.stat(full_path)
            # metadata.read()
            # print(metadata)
            # name, extension = os.path.splitext(image)
            # sub_type = photo.mime_type.split('/')[1]
            # TODO(jreuter): Store this in a variable to be re-used.
            # size_string = str(self._default_size[0]) + \
            #               'x' + str(self._default_size[1])
            # new_folder = 'resized_' + size_string
            # directory = os.path.join(self._folder, new_folder)
            if not os.path.exists(self._new_folder):
                os.makedirs(self._new_folder)
            outfile = photo['output']
            # outfile = os.path.join(self._new_folder,
            #                        name + '_' + self._size_string + '.JPG')
            # logging.info('creating file for %s.' % outfile)
            logging.info(f"{bcolors.OKGREEN}Creating file for {outfile}{bcolors.ENDC}")
            im.thumbnail(self._default_size, Image.ANTIALIAS)
            im.save(outfile, 'jpeg')
            # TODO(jreuter): Split this out to a function.
            # outfile_metadata = pyexiv2.ImageMetadata(outfile)
            outfile_metadata = Metadata(outfile)
            # outfile_metadata.read()
            # We check for Tiff images.  If found, don't save comment data.
            if metadata.get_mime_type() == 'image/tiff':
                # params: destination, exif=True, iptc=True,
                # xmp=True, comment=True
                # metadata.copy(outfile_metadata, True, True, True, False)
                # save all exif data of orinal image to resized
                for tag in metadata.get_exif_tags():
                    logging.info("setting tag {} in file {}.".format(tag, outfile))
                    outfile_metadata[tag] = metadata[tag]
            else:
                for tag in metadata.get_exif_tags():
                    logging.info("setting tag {} in file {}.".format(tag, outfile))
                    outfile_metadata[tag] = metadata[tag]
            outfile_metadata.save_file(outfile)
            # os.utime(outfile, (stinfo.st_atime, stinfo.st_mtime))
        except IOError:
            logging.error(f"{bcolors.FAIL}Cannot create new image for {photo['input']}{bcolors.ENDC}")
            # logging.error('Cannot create new image for %s.' % photo['input'])

    def convert_video(self, video):
        """
        Converts one video using HandBrakeCLI.  This currently only works on
        linux since it builds a full path to the binary in /usr/bin/.

        :param video: Video file to convert.
        :param mime: MimeType string of file.
        """
        try:
            print(f"{bcolors.OKCYAN}Processing file {video['input']} now.{bcolors.ENDC}")
            cores_to_use = max(cpu_count()-2, 1)
            thread_count = f"threads={cores_to_use}"
            if not os.path.exists(self._new_folder):
                os.makedirs(self._new_folder)
            handbrake_command = [
                os.path.join(os.path.sep, 'usr', 'bin', 'HandBrakeCLI'),
                '-v',
                '-x', thread_count,
                '-e', 'x264',
                '-t', '1',
                '--h264-profile', 'main',
                '--x264-preset', 'slower',
                '--quality', '21',
                '-i', video['full_path'],
                '-o', video['output']
            ]
            logging.info(f"cmd is {handbrake_command}")
            logging.debug(f"Creating file {video['output']}")
            handbrake = subprocess.Popen(
                handbrake_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, err = handbrake.communicate()
            # if handbrake.returncode or err:
                # Handbrake is returning errors that aren't really errors and I can't figure out an option to stop it.
                # logging.error('Error from Handbrake %s.' % err)
                # return
            logging.info(f"Done with video: {video['output']}")
            # logging.info('Done with video: %s.' % video['output'])
        except OSError as ex:
            logging.error(f"{bcolors.FAIL}OS Error: {ex}{bcolors.ENDC}")
            # logging.error('OS Error: %s.' % ex)
        except IOError:
            logging.error(f"{bcolors.FAIL}Cannot create new video for {video['input']}{bcolors.ENDC}")
            # logging.error('Cannot create new video for %s.' % video['input'])

    def do_converstion(self, medium):
        print("Starting process for medium: %s." % medium)
        # Get mime type (I hate that it's called magic).
        # TODO(jreuter): Can we pull mimetype from pyexiv2?
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(os.path.join(self._folder, medium))
        # If it's an image, pass to the image resizer.
        # TODO(jreuter): Make this smarter since we can't process all types
        # of images.
        print("We are comparing this mime type {} for file {}".format(mime_type, medium))
        if mime_type.startswith('image'):
            self.resize_image(medium, mime_type)
        elif mime_type.startswith('video'):
            # TODO(jreuter): Queue videos and convert later.
            # full_path = os.path.join(self._folder, medium)
            # stinfo = os.stat(full_path)
            finished_file = self.convert_video(medium, mime_type)
            print("File results for video : %s" % finished_file)
            # os.utime(finished_file, (stinfo.st_atime, stinfo.st_mtime))
        elif mime_type == 'application/octet-stream':
            print("Not processing file {}.".format(medium))
        print("Done processing medium: %s." % medium)

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
            logging.error(f"{bcolors.WARNING}Program only handles folders.{bcolors.ENDC}")
            exit(1)

        # Make sure it's not a dot folder (may be removed later).
        if os.path.basename(self._folder).startswith('.'):
            logging.info(f"{bcolors.WARNING}Ignoring dot folders.{bcolors.ENDC}")
            exit()

        self._size_string = str(self._default_size[0]) + \
                          'x' + str(self._default_size[1])
        self._new_folder = os.path.join(self._folder, 'resized_' + self._size_string)
        if not os.path.exists(self._new_folder):
            os.makedirs(self._new_folder)

        # Get all files in the directory, but only files.
        files = [f for f in os.listdir(self._folder)
                 if os.path.isfile(os.path.join(self._folder, f))]

        videos = []     # os.path.join(self._new_folder, name + '_compressed' + '.m4v')
        photos = []     # os.path.join(self._new_folder, name + '_' + self._size_string + '.JPG')
        for file in files:
            name, extension = os.path.splitext(file)
            source_full_path = os.path.join(self._folder, file)
            # TODO(jreuter): Can we pull mimetype from pyexiv2?
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(source_full_path)
            stinfo = os.stat(source_full_path)
            if mime_type.startswith('image'):
                photos.append({
                    "input": file,
                    "full_path": source_full_path,
                    "mime_type": mime_type,
                    "timestamp_accessed": stinfo.st_atime,
                    "timestamp_modified": stinfo.st_mtime,
                    "output": os.path.join(self._new_folder, name + '_' + self._size_string + '.JPG')
                })
            elif mime_type.startswith('video'):
                videos.append({
                    "input": file,
                    "full_path": source_full_path,
                    "mime_type": mime_type,
                    "timestamp_accessed": stinfo.st_atime,
                    "timestamp_modified": stinfo.st_mtime,
                    "output": os.path.join(self._new_folder, name + '_compressed' + '.m4v')
                })
            elif mime_type == 'application/octet-stream':
                print(f"{bcolors.WARNING}Not processing file {file}.{bcolors.ENDC}")

        print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Processing Photos.{bcolors.ENDC}")
        # Loop through file list for processing.
        pool = Pool(max(cpu_count()-2, 1), limit_cpu)
        results = pool.map(unwrap_self_photos, list(zip([self]*len(photos), photos)))

        print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Adjusting photo timestamps.{bcolors.ENDC}")
        for photo in photos:
            stinfo = os.stat(photo['output'])
            os.utime(photo['output'], (stinfo.st_atime, photo['timestamp_modified']))

        print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Processing Videos.{bcolors.ENDC}")
        # Loop through file list for processing.
        pool = Pool(max(cpu_count() - 2, 1), limit_cpu)
        results = pool.map(unwrap_self_videos, list(zip([self] * len(videos), videos)))

        print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Adjusting video timestamps.{bcolors.ENDC}")
        for video in videos:
            stinfo = os.stat(video['output'])
            os.utime(video['output'], (stinfo.st_atime, video['timestamp_modified']))

        print(f"{bcolors.OKGREEN}Finished processing media.{bcolors.ENDC}")


if __name__ == '__main__':
    MediaResizer().main()
