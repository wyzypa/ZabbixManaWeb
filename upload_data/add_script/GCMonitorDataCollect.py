#! /usr/bin/python
import os
FILE = '/tmp/JavaGCMonitorDataFile'
def main():
	if not os.path.isfile(FILE):
		print "Cannot find data file!"
	else:
		fi = open(FILE,"r")
		print fi.read()
		fi.close()

if __name__ == "__main__":
	main()

