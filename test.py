import cv2 
import numpy as np


img = cv2.imread( "button.png" )
print( img.shape )
img = img[0:400, 0:800]





cv2.imshow( "asdgasdg", img)
cv2.waitKey(0)