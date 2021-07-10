import tkinter
from tkinter.constants import E
import pygame
from torch._C import clear_autocast_cache
import phu_yolov5
import cv2

from pygame import key
from pygame.locals import *
from tkinter import filedialog

pygame.init()

width = 1280
height = 720
window = pygame.display.set_mode( (width, height), 0, 32)
pygame.display.set_caption( "alo" )


def ask_videoPath( ):
	tklib = tkinter.Tk()
	tklib.withdraw()
	path = filedialog.askopenfilename( initialdir="./", title="choose a video file")
	tklib.destroy()
	return path

def endGame( ):
	pygame.quit()
	cv2.destroyAllWindows()
	phu_yolov5.quit()
	exit(0)

class Button():
	def __init__( self, img_path, size, pos=( 0,0 ) ) :
		self.sur = phu_yolov5.cv2_img2sur( cv2.imread(img_path))
		self.sur = phu_yolov5.resize_surface_withMax( self.sur, size )
		self.rect = self.sur.get_rect()
		self.rect.x, self.rect.y = pos 
	
	def isClick( self, event ):
		mouse_x, mouse_y = pygame.mouse.get_pos()
		if event.type == MOUSEBUTTONDOWN:
			if pygame.mouse.get_pressed()[0]:
				if self.rect.collidepoint( mouse_x, mouse_y ):
					return True
		return False
	
	def set_pos(self, base_size, x="left", y="top" ):
		wi, hi = base_size
		if x =="left":
			self.rect.x = 0
		elif x == "center":
			self.rect.x = (wi//2) - (self.rect.w//2) 
		elif x == "right":
			self.rect.x = wi - self.rect.w

		if y =="top":
			self.rect.y = 0
		elif y == "center":
			self.rect.y = (hi//2) - (self.rect.h//2) 
		elif y == "bottom":
			self.rect.y = hi - self.rect.h

	def show( self, base ):
		base.blit( self.sur, self.rect )

class SwitcingButton( Button ):
	def __init__(self, img_paths , size, pos=(0,0) ):
		path1, path2 = img_paths
		Button.__init__( self, path1 , size, pos )
		self.otherSur = phu_yolov5.cv2_img2sur( cv2.imread(path2) )
		self.otherSur = phu_yolov5.resize_surface_withMax( self.otherSur, size )
	
	# state's type is boolean
	def show( self, base, state = True ):
		if state :
			base.blit( self.sur, self.rect )
		else :
			base.blit( self.otherSur, self.rect )

playing = False
# play_but = Button( "play.png", 50, (600,0) )
play_but = SwitcingButton( ("play.png","pause.png"), 50 )
play_but.set_pos( (width,height), "center", "bottom" )

video_but = Button( "video.png", 200)
webcam_but = Button( "webcam.png", 200, ( 0, 100 ))
youtube_but = Button( "youtube.png", 200, ( 0,200 ) )
import clipboard
import pafy

catching_but = SwitcingButton( ("catching.png", "non-catching.png"), 300, ( 0, 300 ))
catching = False

import torch
model = torch.hub.load( "./yolov5", "custom", "./biker_yolov5s.pt", source="local")
mainCam = phu_yolov5.Camera(model, 0, 30 )
mainFilter = phu_yolov5.Filter( model )


# threading handle event
while 1 :
	# # checking event
	for event in pygame.event.get():
		if event.type == QUIT:
			endGame()
		elif play_but.isClick( event ):
			playing = not playing
		elif video_but.isClick( event ):
			path = ask_videoPath()
			mainCam.change_source( path )
		elif webcam_but.isClick( event ):
			mainCam.change_source( 0 )
		elif youtube_but.isClick( event ):
			#print url
			link = clipboard.paste()
			video = pafy.new(link)
			best = video.getbest(preftype="mp4")
			mainCam.change_source( best.url )
		elif catching_but.isClick( event ):
			catching = not catching
			mainCam.switch_catching()

	
	window.fill([0,0,0])
	# window.blit( kakashi, rect)

	if playing :
		mainCam.show( window )

	# if playing:
	# 	ret, frame = cap.read()
	# 	sur = cv2_img2sur( frame )
	# 	sur = resize_surface_withMax( sur , 800)
	# 	rect = sur.get_rect()
	# 	window.blit( sur, rect )

	play_but.show( window, playing )
	video_but.show( window )
	webcam_but.show( window )
	youtube_but.show( window )
	catching_but.show( window, catching)

	pygame.display.update()

