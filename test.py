import cv2 
import numpy as np
import time 
import sys, getopt


def main( argv ):
	opts, args = getopt.getopt( argv, "hi:o", ["youtube", "video" ] )

	path = ""
	for opt, arg in opts:
		if opt in ("-y","--youtube"):
			



if __name__ == "__main__":
	main( sys.argv[1:] )
