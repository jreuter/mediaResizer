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
    -h --help               Show this screen.
    --version               Show version.
    -q                      Quiet the logging to only ERROR level.
    -v                      Verbose output (INFO level).
    --photos-only           Skip video encoding.
    --videos-only           Skip photo encoding.
    --time-shift=<+/-hours> Plus or Minus hours on the creation time.
    --debug                 Very Verbose output (DEBUG level).
"""
# from datetime import timezone, datetime, tzinfo, timedelta
# import pytz
# from zoneinfo import ZoneInfo
from datetime import timezone, datetime, tzinfo, timedelta, time

import exiftool
import pytz

from docopt import docopt
import logging
import magic
import os
import psutil
from PIL import Image
import gi
gi.require_version('GExiv2', '0.10')
from gi.repository.GExiv2 import Metadata
# import exiftool
from exiftool import ExifToolHelper
# import exiv2
from pymediainfo import MediaInfo
import ffmpeg
import subprocess
from multiprocessing import Pool, cpu_count, Queue, Process



def limit_cpu():
    "is called at every process start to lower the process priority."
    p = psutil.Process(os.getpid())
    # set to lowest priority, this is windows only, on Unix use ps.nice(19)
    # p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    p.nice(19)


def unwrap_self_photos(arg, **kwarg):
    return MediaResizer.resize_image(*arg, **kwarg)


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
    _process_photos = True
    _process_videos = True
    _time_shift = 0

    def __init__(self):
        """
        Gets command line arguments using docopt and sets logging level.
        """
        self._arguments = docopt(__doc__, version='0.1')
        self._set_logging_verbosity()
        if self._arguments['--photos-only']:
            self._process_videos = False
        if self._arguments['--videos-only']:
            self._process_photos = False
        if self._arguments['--time-shift']:
            self._time_shift = int(self._arguments['--time-shift'])

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

    def consume_video(self, queue):
        while True:
            item = queue.get()
            if item is None:
                break
            self.convert_video(item)

    def resize_image(self, photo):
        """
        Resizes a single image.  Uses the mime type to determine what type of
        image to save and uses the file extension of the original in the new
        one.  This will need updated when the ability to output to a different
        format from the input is added.

        :param photo: Dict with the following fields:
                    "input": filename,
                    "full_path": source full_path,
                    "mime_type": source mime_type,
                    "timestamp_accessed": source stinfo.st_atime,
                    "timestamp_modified": source stinfo.st_mtime,
                    "output": output file with full path
        """
        try:
            print(f"{bcolors.OKCYAN}Processing file {photo['input']} now.{bcolors.ENDC}")
            im = Image.open(photo['full_path'])
            metadata = Metadata(photo['full_path'])
            if not os.path.exists(self._new_folder):
                os.makedirs(self._new_folder)
            outfile = photo['output']
            logging.info(f"{bcolors.OKGREEN}Creating file for {outfile}{bcolors.ENDC}")
            im.thumbnail(self._default_size, Image.ANTIALIAS)
            im.save(outfile, 'jpeg')
            # TODO(jreuter): Split this out to a function.
            outfile_metadata = Metadata(outfile)
            # We check for Tiff images.  If found, don't save comment data.
            if metadata.get_mime_type() == 'image/tiff':
                # TODO (jreuter): See if we really need this.  I can't remember what we did differently with TIFF.
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
        except IOError:
            logging.error(f"{bcolors.FAIL}Cannot create new image for {photo['input']}{bcolors.ENDC}")

    def convert_video(self, video):
        """
        Converts one video using HandBrakeCLI.  This currently only works on
        linux since it builds a full path to the binary in /usr/bin/.

        :param video: Dict with the following fields:
                    "input": filename,
                    "full_path": source full_path,
                    "mime_type": source mime_typ    e,
                    "timestamp_accessed": source stinfo.st_atime,
                    "timestamp_modified": source stinfo.st_mtime,
                    "output": output file with full path
        """
        try:
            print(f"{bcolors.OKCYAN}Processing file {video['input']} now.{bcolors.ENDC}")
            # print(f"Timestamp is {video['timestamp_modified']}")
            cores_to_use = max(cpu_count()-2, 1)
            thread_count = f"threads={cores_to_use}"
            if not os.path.exists(self._new_folder):
                os.makedirs(self._new_folder)

            # # Getting Exif Data from original file.
            # print(f"\nExif data for file {video['full_path']}\n")
            # with ExifToolHelper() as eh:
            #     for tag in eh.get_metadata(video['full_path']):
            #         for k, v in tag.items():
            #             print(f"Dict {k}: {v}")

            all_metadata = ""
            for k, v in video['source_exif'].items():
                all_metadata += str(f"{k}={v} ")
                # all_metadata += str(f"** {'-metadata': '{k}={v}'},")
            all_metadata = all_metadata[:-1]

            # fmt_string = "%Y-%m-%d %H:%M:%S"
            # I did have this option **{'c:v': 'libx264'}, **{'c:a': 'copy'},  but ffmpeg didn't like video from the T5i
            ffmpeg.input(video['full_path']).output(video['output'],
                                                    metadata=f"creation_time={video['timestamp_modified']}",
                                                    **{'c:v': 'libx264'},
                                                    loglevel="quiet",
                                                    movflags='faststart',
                                                    preset='slower', crf=21).overwrite_output().run()

            # handbrake_command = [
            #     os.path.join(os.path.sep, 'usr', 'bin', 'HandBrakeCLI'),
            #     '-v',
            #     '-x', thread_count,
            #     '-e', 'x264',
            #     '-t', '1',
            #     '--h264-profile', 'main',
            #     '--x264-preset', 'slower',
            #     '--quality', '21',
            #     '-i', video['full_path'],
            #     '-o', video['output']
            # ]
            # logging.info(f"cmd is {handbrake_command}")
            # logging.debug(f"Creating file {video['output']}")
            # handbrake = subprocess.Popen(
            #     handbrake_command,
            #     stdout=subprocess.PIPE,
            #     stderr=subprocess.PIPE
            # )
            # out, err = handbrake.communicate()
            # TODO (jreuter): See if there's a way to add this back and not get errors that aren't really errors.
            # if handbrake.returncode or err:
                # Handbrake is returning errors that aren't really errors and I can't figure out an option to stop it.
                # logging.error('Error from Handbrake %s.' % err)
                # return
            logging.info(f"Done with video: {video['output']}")
        except OSError as ex:
            logging.error(f"{bcolors.FAIL}OS Error: {ex}{bcolors.ENDC}")
        except IOError:
            logging.error(f"{bcolors.FAIL}Cannot create new video for {video['input']}{bcolors.ENDC}")

    def do_converstion(self, files):
        videos = []  # os.path.join(self._new_folder, name + '_compressed' + '.m4v')
        photos = []  # os.path.join(self._new_folder, name + '_' + self._size_string + '.JPG')
        for file in files:
            name, extension = os.path.splitext(file)
            source_full_path = os.path.join(self._folder, file)
            # TODO(jreuter): Can we pull mimetype from pyexiv2?
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(source_full_path)
            stinfo = os.stat(source_full_path)
            # time = (datetime.fromtimestamp(stinfo.st_mtime, tz=ZoneInfo("America/New York")))
            # est = pytz.timezone('US/Eastern')
            # time = (datetime.fromtimestamp(stinfo.st_mtime, tz=est))
            # TODO (Jarrod): Make the timezone a new flag option for this code.
            # dt = datetime.fromtimestamp(stinfo.st_mtime, tz=pytz.timezone('US/Eastern'))
            # time = (datetime.fromtimestamp(stinfo.st_mtime)
            #         + timedelta(hours=self._time_shift))
            dt = (datetime.fromtimestamp(stinfo.st_mtime, tz=pytz.timezone('US/Eastern'))
                    + timedelta(hours=self._time_shift))
            if mime_type.startswith('image'):
                photos.append({
                    "input": file,
                    "full_path": source_full_path,
                    "mime_type": mime_type,
                    "timestamp_accessed": stinfo.st_atime,
                    "timestamp_modified": dt.timestamp(),
                    "output": os.path.join(self._new_folder, name + '_' + self._size_string + '.JPG')
                })
            elif mime_type.startswith('video'):
                # Getting Exif Data from original file.
                with ExifToolHelper() as eh:
                    tag = eh.get_metadata(source_full_path)[0]
                    # Can print for debugging like below.
                    # for tag in eh.get_metadata(source_full_path):
                    #     print(f"tag is : {tag}")
                    # for k, v in tag.items():
                    #     print(f"Dict {k}: {v}")

                videos.append({
                    "input": file,
                    "full_path": source_full_path,
                    "mime_type": mime_type,
                    "timestamp_accessed": stinfo.st_atime,
                    "timestamp_modified": dt.timestamp(),
                    "source_exif": tag,
                    "output": os.path.join(self._new_folder, name + '_compressed' + '.m4v')
                })
            elif mime_type == 'application/octet-stream':
                print(f"{bcolors.WARNING}Not processing file {file}.{bcolors.ENDC}")

        if self._process_photos:
            print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Processing Photos.{bcolors.ENDC}")
            # Loop through file list for processing.
            pool = Pool(max(cpu_count() - 2, 1), limit_cpu)
            results = pool.map(unwrap_self_photos, list(zip([self] * len(photos), photos)))

            print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Adjusting photo timestamps.{bcolors.ENDC}")
            for photo in photos:
                stinfo = os.stat(photo['output'])
                os.utime(photo['output'], (stinfo.st_atime, photo['timestamp_modified']))
        else:
            print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Photo Processing Skipped.{bcolors.ENDC}")

        if self._process_videos:
            print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Processing Videos.{bcolors.ENDC}")
            # Loop through file list for processing.
            queue = Queue()
            for video in videos:
                queue.put(video)
            queue.put(None)
            video_process = Process(target=self.consume_video, args=(queue,))
            video_process.start()
            video_process.join()

            print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Adjusting video timestamps.{bcolors.ENDC}")
            for video in videos:
                with ExifToolHelper() as eh:
                    eh.__init__(check_tag_names=False)
                    # eh.execute("-api QuickTimeUTC=1")
                    eh.execute(
                        "-tagsfromfile", f"{video['full_path']}", f"{video['output']}", "-overwrite_original"
                    )
                    # timestamp = datetime(video['timestamp_modified']).strftime("%Y-%m-%d %H:%M:%S%z")
                    # timestamp = video['timestamp_modified'].strftime("%Y-%m-%d %H:%M:%S%z")
                    # timestamp = time.strftime("%Y-%m-%d %H:%M:%S%z", video['timestamp_modified'])
                    # print(f"timestamp is : {video['source_exif']['QuickTime:CreateDate']}")
                    # eh.execute("-api QuickTimeUTC=1",)
                    # stinfo = os.stat(video['output'])
                    # os.utime(video['output'], (stinfo.st_atime, video['timestamp_modified']))
                    eh.execute(
                        f"-DateTimeOriginal={video['source_exif']['QuickTime:CreateDate']}",
                        f"{video['output']}", "-overwrite_original"
                    )
                    ## TODO: Test this, it didn't look like it worked as expected.
                    # if self._time_shift < 0:
                    #     eh.execute(
                    #         f"-AllDates+={self._time_shift}", f"{video['output']}"
                    #     )
                    # elif self._time_shift > 0:
                    #     eh.execute(
                    #         f"-AllDates+={-self._time_shift}", f"{video['output']}"
                    #     )
                stinfo = os.stat(video['output'])
                os.utime(video['output'], (stinfo.st_atime, video['timestamp_modified']))
                # subprocess.run(
                #     ["exiftool", "-tagsfromfile", f"{video['full_path']}", f"{video['output']}"]
                # )
                # print(f"\nExif data for file {video['output']}\n")
                # with ExifToolHelper() as eh:
                #     eh.__init__(check_tag_names=False)
                #     output_tag = eh.get_metadata(video['output'])[0]
                #     # # Can print for debugging like below.
                #     # for tag in eh.get_metadata(video['output']):
                #     #     print(f"tag is : {tag}")
                #     #     for k, v in tag.items():
                #     #         print(f"Dict {k}: {v}")
                #     output_exif_keys = list(output_tag.keys())
                #     new_exif_data = {}
                #     print(f"Source exif data: {video['source_exif']}")
                #     for k, v in video['source_exif'].items():
                #         print(f"Tag is {k} : {v}")
                        # print(f"Checking key {k} is in list {output_exif_keys}")
                #         if k not in output_exif_keys:
                #             print(f"Adding {k} to output")
                #             new_exif_data[str(k)] = v
                #             # eh.set_tags(video['output'],tags={k:v},params=["-P", "-overwrite_original"])
                #     # print(f"New tags are : {new_exif_data}")
                #     # print(f"Video file is : {video['output']}")
                #     eh.set_tags(video['output'],tags=new_exif_data)
                #     # ,params=["-P", "-overwrite_original"])
                #     # for k, v in new_exif_data.items():
                #     #     eh.set_tags([video['output']],tags={str(k):v},params=["-P", "-overwrite_original"])

                # stinfo = os.stat(video['output'])
                # os.utime(video['output'], (stinfo.st_atime, video['timestamp_modified']))

                # mp4 = MP4(video['output'])
                # print(f"Tags: {mp4.pprint()}")
                # metadata = Metadata(video['output'])
                # print(f"Tags: {metadata.get_exif_tags()}")
                # media_info = MediaInfo.parse(video['output'])
                # general_track = media_info.general_tracks[0]
                # print(f"Tags: {media_info.to_data()}")
                # for track in media_info.tracks:
                #     track.encoded_date = video['timestamp_modified']
                # ffmpeg.input(video['output']).output(video['output'], metadata='creation_time=2015-10-21 07:28:00', map=0,
                #                                      c='copy').overwrite_output().run()
        else:
            print(f"\n{bcolors.UNDERLINE}{bcolors.OKGREEN}Video Processing Skipped.{bcolors.ENDC}")

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

        self.do_converstion(files)
        print(f"{bcolors.OKGREEN}Finished processing media.{bcolors.ENDC}")


if __name__ == '__main__':
    MediaResizer().main()
