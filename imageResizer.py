#!/usr/bin/env python
# encoding: utf-8
# Copyright 2014-2015 Jarrod Reuter

import magic
import os
from PIL import Image
import pyexiv2
import threading

class ImageResizer(threading.Thread):
	"""docstring for ImageResizer"""
	def __init__(self, image, mime, image_dir, dimensions):
		# super(ImageResizer, self).__init__()
		threading.Thread.__init__(self)
		self.image = image
		self.mime = mime
		self.image_dir = image_dir
		self.dimensions = dimensions

	def run(self):
		print "Starting thread for image: %s." % self.image
		try:
			full_path = os.path.join(self.image_dir, self.image)
			im = Image.open(full_path)
			# TODO(jreuter): Split this to a function.
			metadata = pyexiv2.ImageMetadata(full_path)
			metadata.read()
			name, extension = os.path.splitext(self.image)
			sub_type = self.mime.split('/')[1]
			# TODO(jreuter): Store this in a variable to be re-used.
			size_string = str(self.dimensions[0]) + \
							  'x' + str(self.dimensions[1])
			new_folder = 'resized_' + size_string
			directory = os.path.join(self.image_dir, new_folder)
			outfile = os.path.join(directory,
				name + '_' + size_string + extension)
			# logging.info('creating file for %s.' % outfile)
			im.thumbnail(self.dimensions, Image.ANTIALIAS)
			im.save(outfile, sub_type.upper())
			outfile_metadata = pyexiv2.ImageMetadata(outfile)
			# TODO(jreuter): Split this out to a function.
			outfile_metadata.read()
			metadata.copy(outfile_metadata)
			outfile_metadata.write()
		except IOError:
			logging.error('Cannot create new image for %s.' % self.image)
		print "Closing thread for image: %s." % self.image
