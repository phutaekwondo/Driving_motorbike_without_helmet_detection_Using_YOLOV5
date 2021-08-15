import cv2, time
import numpy as np
from threading import Thread
import os
from queue import Queue



# Detection format
# xmin ymin xmax ymax confidence class
# 0.x  0.y  0.x  0.y  0.c        0( or 1,2,... )  

def same_object( box1, box2, thresh=0.5 ):
	x1,y1,w1,h1 = box1
	x2,y2,w2,h2 = box2

	inner = min( x1+w1-x2 , x2+w2-x1 ) * min( y1+h1-y2, y2+h2-y1 )
	total = w1*h1 + w2*h2 - inner
	fra = inner / total

	return fra >= thresh

def detection_filter( detection ):
	if len( detection ) == 0 : return detection

	hel = []
	nohel = []
	biker = []

	# split hel boxes anh nohel boxes
	for box in detection:
		if box[5] == 0:
			nohel.append( box )
		elif box[5] == 1:
			hel.append( box )
		else :
			biker.append( box )

	# two arrays below contains indexes locate boxes we wanna take
	hel_av = []
	nohel_av = [ i for i in range(len(nohel)) ]
	for i in range( len(hel) ):
		hel_con = hel[i][4]
		hel_box = (hel[i][0],hel[i][1],hel[i][2],hel[i][3])
		av = True
		nav = nohel_av
		for ni in nav:
			noh_con = nohel[ni][4]
			noh_box = (nohel[ni][0],nohel[ni][1],nohel[ni][2],nohel[ni][3])
			if same_object( hel_box, noh_box ):
				if hel_con >= noh_con:
					nohel_av.remove(ni)
				else:
					av = False
		if av:
			hel_av.append( i )

	return [hel[i] for i in hel_av] + [nohel[x] for x in nohel_av] + biker

def draw_boxes( img, detection ):
	if len( detection ) == 0: return img

	de = [box.astype(int) for box in detection]
	colors = [(0,0,255), (0,255,0), (255,255,0)]
	h,w,_ = img.shape

	thick = h//700 + 2
	for box in de:
		img = cv2.rectangle( img, (box[0],box[1]), (box[2],box[3]), colors[box[5]] , thick )
	return img

def count_class( detection, target=0 ):
	if len( detection ) == 0 : return 0
	count = 0
	for box in detection :
		if box[5] == target:
			count += 1
	return count

# general
def get_detection( img, model, get_count = False ):
	# convert to yolo format anh predict
	img = cv2.cvtColor( img, cv2.COLOR_BGR2RGB )
	res = model(img)

	# get detection for filter anh draw boxes
	detection = res.xyxy[0].cpu().numpy()

	detection = detection_filter( detection )
	if not get_count:
		return detection
	else :
		return detection, count_class( detection )

def detect( img, model, get_count = False  ):
	# get detection for drawing
	detection = get_detection( img, model )
	img = draw_boxes( img, detection)

	# return cv2 img has boxes on it
	if not get_count:
		return img
	else :
		return img, count_class( detection )


class Camera( object ):
	def __init__( self, model, source=0, FPS=60, catching = False  ):
		self.detective = Detective( model, catching )
		self.cap = cv2.VideoCapture( source ) 
		self.SPF = 1/FPS
		self.FPS = 60 

		_, self.frame = self.cap.read()

		self.threading = Thread( target=self.update, args=() )
		self.threading.daemon = True 
		self.threading.start()

	def update( self ):
		while 1:
			if self.cap.isOpened( ):
				ret, img = self.cap.read()
				if ret:
					self.frame = img 
				
				cv2.waitKey( 1000//self.FPS )
				
	
	def read_predicted_frame( self ):
		img = self.frame.copy()

		boxes = self.detective.detect( img )

		img = draw_boxes( img, boxes )

		return img
	
	
	def read_real_frame( self ):
		return self.frame

# this Q below containing all catched images
waitingQ = Queue()

class Detective( object ):
	def __init__( self, model, catching = False, savedir="saved/", filetag="" ):
		self.model = model
		self.catching = catching

		self.filter = Filter( model, savedir, filetag )
		
		self.nohel_count_old = 0
		self.biker_nohel_count = 0

	def detect( self, img ):
		# take img

		# detecting 
		boxes = get_detection( img, self.model)

		# for catching 
		if self.catching :
			biker_which_has_nohel = self.filter.nohels_inside_biker( boxes )
			biker_nohel_count = len( biker_which_has_nohel )
			if biker_nohel_count > self.biker_nohel_count:
				## catch
				waitingQ.put( (img.copy(), biker_which_has_nohel) )
				# print( "add an image to waitingQ")
			## update counting
			self.biker_nohel_count = biker_nohel_count
		
		return boxes ## for camera drawing box 
	
	def switch_catching( self ):
		self.catching = not self.catching
		self.nohel_count_old = 0
		self.biker_nohel_count = 0

## this below class will decide which images in waitingQ allowed to save
class Filter( object ):
	def __init__( self, model, savedir="saved/", tag="" ):
                self.model = model
                self.savedir = savedir
                if not os.path.isdir( savedir ):
                	os.mkdir( savedir )
                self.tag = tag
                
                self.threading = Thread( target=self.run, args=())
                self.threading.daemon = True
                self.threading.start()
	
	def save_img( self, img ):
                ## make a new file's name
                ### the below loop will check if file's name is existed, then make a new name
                index = 0
                while os.path.isfile( self.savedir + self.tag + str(index) + ".jpg" ):
                	index += 1
                filename = self.savedir + self.tag + str(index) + ".jpg"
                
                ## save img by a name 
                cv2.imwrite( filename, img )
                
                ## addname to savedNames list
                print( "saved to " + filename )
	
	def run( self ):
		def recheck( img, thresh = 0.9 ):
			## get img's area
			h,w,_ = img.shape
			whole_area = h*w

			boxes = get_detection( img, self.model )

			nohel_count = count_class( boxes, 0)
			biker_count = count_class( boxes, 2)
			## if don't have nohelmet or biker anymore, then return False
			for count in [nohel_count, biker_count]:
				if count == 0:
					# print("it's not because \"nohelmet NOT FOUND\"\n")
					return False
			
			## if there are not a biker fit the img
			for box in boxes:
				if box[5] == 2:
					xmin,ymin,xmax,ymax,_,__ = box
					area = (ymax-ymin)*(xmax-xmin)
					if (area/whole_area) >= thresh:
						return True
			
			# print("it's not because \"biker NOT FOUND\"\n" )
			return False

		def get_padding( box, width,height, padding = 5 ):
			xmin,ymin,xmax,ymax,_,__ = box.astype(int)
			xmin -= padding
			ymin -= padding
			xmax += padding
			ymax += padding

			if xmin < 0 : xmin = 0
			if ymin < 0 : ymin = 0
			if xmax > width : xmax = width
			if ymax > height : ymax = height

			return xmin,ymin,xmax,ymax,_,__

		## work while waitingQ is not empty
		while 1:
			# if not waitingQ.empty():
				## take (img, boxes) from waitingQ
				img, bikers= waitingQ.get()
				img_h, img_w, img_d = img.shape

				## check if nohels is inside biker
				## bikers get from waitingQ
				# bikers = self.nohels_inside_biker( boxes )

				## if cropped img still has biker, nohelmet, then save it 
				for biker in bikers:
					padding = 10
					xmin,ymin,xmax,ymax,_,__ = get_padding( biker, img_w, img_h, padding=padding )
					biker_img = img[ ymin:ymax, xmin:xmax ]

					thresh = ( (biker[3]-biker[1])/(ymax - ymin) ) * ( (biker[2]-biker[0])/(xmax-xmin) ) - 0.2

					# print( "\nMakesure-checking a nohelmet-biker... ")
					if recheck( biker_img, thresh=thresh ):
						self.save_img( biker_img )
						# print( "It is. Saved a nohelmet-biker.")
					# else:
					# 	print( "It's not.")


	def inside( self, box1, box2, thresh=0.8 ):
		## return (box1 inside box2)?
		xmin, ymin, xmax, ymax, con, class_index = box1
		whole_area = (xmax-xmin) * (ymax-ymin)

		## get parameter of inside box
		xmin2, ymin2, xmax2, ymax2, con, class_index = box2

		## get w,h of inside rect
		def get_inner( min1,max1, min2,max2 ):
			dis1 = max1 - min2
			dis2 = max2 - min1
			if dis1*dis2 <= 0:
				return 0
			if dis1>dis2:
				return dis2
			return dis1
		
		w = get_inner( xmin, xmax, xmin2, xmax2 )
		h = get_inner( ymin, ymax, ymin2, ymax2 )

		## calculate inside area
		inside_area = w * h

		return ( inside_area/whole_area )>= thresh


	def nohels_inside_biker( self, boxes ):
		## take nohelmets and bikers from whole
		nohels = [ box for box in boxes if box[5] == 0]
		bikers = [ box for box in boxes if box[5] == 2]

		## this below list will contain return bikers
		res = []

		## for each of biker objects
		for biker in bikers:
			## if biker has nohelmet, then add it to res
			add = False
			i=0
			## for each of nohels
			while not add and i<len(nohels):
				if self.inside( nohels[i], biker ):
					add = True
				i+=1 
			if add :
				res.append( biker )

		### this function will return list of bikers has nohelmet
		return res

def quit( ):
	exit(0)


