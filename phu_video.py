import phu_yolov5
import sys, getopt
import torch
import cv2, time
import pafy


def main( argv ):
	# arg check
	opts, args = getopt.getopt( argv, "yvcm" , ["youtube=", "video=", "catching=","model="] )
	print( opts )

	catching = False
	source = None
	model_path = "biker_yolov5s.pt"
	for opt, arg in opts:
		if opt in ("-y","--youtube"):
			video = pafy.new( arg )
			best = video.getbest( preftype="mp4" )
			source = best.url
		elif opt in ("-v","--video"):
			source = arg
		elif opt in ("-c","--catching"):
			if arg == "1":
				catching = True
			else :
				catching = False
		elif opt in ("-m","--model"):
			model_path = arg

	if source == None :
		source = 0 

	print( "using source :", source )
	print( "using model : "+model_path)
	
	cap = cv2.VideoCapture( source )

	model = torch.hub.load( "./yolov5", "custom", model_path, source="local")
	detective = phu_yolov5.Detective( model, catching=catching )
	mainFilter = phu_yolov5.Filter( model )

	FPS =  60
	SPF = 1/FPS

	while 1:
		start_time = time.time()
		ret, frame = cap.read()

		boxes = detective.detect( frame )
		img = phu_yolov5.draw_boxes( frame, boxes )

		cv2.imshow( "asfgas", img )
		if cv2.waitKey(1) == ord( "q" ):
			break

		run_time = time.time() - start_time

		if source != 0:
			if run_time < SPF:
				time.sleep( SPF - run_time )
			else:
				passframe = round( run_time/SPF ) - 1
				current_frame = cap.get( cv2.CAP_PROP_POS_FRAMES )
				cap.set( cv2.CAP_PROP_POS_FRAMES, current_frame + passframe )

	cv2.destroyAllWindows()


if __name__ == "__main__":
	main( sys.argv[1:] )


