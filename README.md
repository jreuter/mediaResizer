# mediaResizer

This code is designed to batch resize images and process videos.  The end
goal is to make a reasonably easy configuration system and sane defaults to
batch process images and video from DSLRs.  Eventually, this will support
users with two different work flows:

1.  A service watching a directory for any new folders for batch processing.

2.  An addition to the context menu on Linux GUIs to process on current
folder.

These two modes, combined with the command-line interface, should support
most users.

## Why make this project?

I used to use a very handy tool with Windows XP which added a context menu to
quickly and easily resize images.  It was written by Microsoft and I used it
daily when processing images for customer websites.  I haven't found a tool
with similar capabilities for Linux and it would also be nice to have the
same functionality on a NAS for processing archives.  My desired work flow
would be dragging a folder to the NAS in which this code would generate
smaller files and automatically upload those to a different server or a
different directory.  I can see this being very useful for photographers and
hobbyists alike.

## Installation

[Ubuntu](docs/install_ubuntu.md)
