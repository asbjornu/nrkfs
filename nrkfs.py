#!/usr/bin/env python

__author__ = "Erlend Klakegg Bergheim <erlend@averlend.com>"
__version__ = "0.1a1"

# Created by Erlend Klakegg Bergheim
# http://blog.averlend.com/

import stat, errno, time

import fuse
from fuse import Fuse

fuse.fuse_python_api = (0, 2)

import nrk

root = nrk.getRoot()

def getNode(path):
	node = root
	for p in path.split("/")[1:]:
		if p != "" and node:
			node = node.getChild(p)
	return node

class Stat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = time.time()
        self.st_mtime = time.time()
        self.st_ctime = time.time()

class NrkFS(Fuse):

	def getattr(self, path):
		st = Stat()
		node = getNode(path)
		if node.isCut():
			st.st_mode = stat.S_IFREG | 0444
			st.st_nlink = 1
			st.st_size = 1000
		elif node:
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 3
		else:
			return -errno.ENOENT
		return st

	def readdir(self, path, offset):
		children = getNode(path).getChildren().keys()
		children.sort()
		for r in [".", ".."] + children:
			yield fuse.Direntry(str(r))

	def open(self, path, flags):
		node = getNode(path)
		if not node.isCut():
			return -errno.ENOENT

	def read(self, path, size, offset):
		node = getNode(path)
		if not node.isCut():
			return -errno.ENOENT

		playlist = """
<?xml version="1.0" encoding="UTF-8"?>
<asx version="3.0">
  <title>NRK Nett-TV</title>
  <author>NRK - Norsk Rikskringkasting</author>
 
  <entry>
    <title>%s</title>
    <ref href="%s" />
  </entry>
</asx>
		""" % (node.title, str(node.getCut()))

		playlist += " " * (1000 - len(playlist))

		# Good help from hello.py in the FUSE project
		slen = len(playlist)
		if offset < slen:
			if offset + size > slen:
				size = slen - offset
			buf = playlist[offset:offset+size]
		else:
			buf = ''
		return buf

if __name__ == '__main__':
    server = NrkFS(version="%prog " + fuse.__version__,
		 usage=Fuse.fusage,
		 dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()
