import kivy
kivy.require('1.7.1')

from kivy.base import EventLoop

EventLoop.ensure_window()

from PIL import Image

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.image import Image as kivyImage
from kivy.core.image import ImageData
from kivy.properties import ObjectProperty

from StringIO import StringIO

from kivy.graphics.texture import Texture

import cv2
import cv
import numpy as np

BLUR_SIZE    = 11
HARRIS_SIZE  = 21
HARRIS_SCALE = 0.3

class VideoToFrames:
    def __init__ (self, path):
        self.path = path
        self.processFrames()

    def createWindows (self):
        cv.NamedWindow('canny')
        #cv.NamedWindow('harris')
        cv.NamedWindow('sobel')
        cv.NamedWindow('output')

        cv.MoveWindow('canny', 0,0)
        #cv.MoveWindow('harris', 650,0)
        cv.MoveWindow('sobel', 1300,0)
        cv.MoveWindow('output', 0,420)
    def talk(self, msg):
        print msg

    def processFrames(self):
        self.vidcap = cv2.VideoCapture( self.path )

        count = 0

        self.image = self.vidcap.read()
        #self.createWindows()

        while True:
            success, image = self.vidcap.read()

            if not success:
                return

            spare = cv.fromarray(image)

            self.image = spare
            return
            size = (spare.width/2, spare.height/2)

            cv.Smooth( spare, spare, cv.CV_GAUSSIAN, BLUR_SIZE, BLUR_SIZE )

            out = cv.CreateImage( size, 8, 3)
            cv.PyrDown(spare, out)

            yuv    = cv.CreateImage( size , 8, 3 )
            gray   = cv.CreateImage( size , 8, 1 )
            canny  = cv.CreateImage( size , 8, 1 )
            sobel  = cv.CreateImage( size , 8, 1 )
            harris = cv.CreateImage( size , cv.IPL_DEPTH_32F, 1 )

            cv.CvtColor( out, yuv, cv.CV_BGR2YCrCb )
            cv.Split( yuv, gray, None, None, None)

            cv.Canny(gray, canny, 50, 200, 3)
            cv.CornerHarris( gray, harris, 3 )
            cv.Sobel( gray, sobel, 1, 0, 3 )

            cv.ConvertScale(canny, canny, -1, 255 )
            cv.ConvertScale(sobel, sobel, -1, 255 )

            for y in range(0, out.height):
                for x in range(0, out.width):
                    harr = cv.Get2D(sobel, y, x)
                    if harr[0] < 10e-06:
                        cv.Circle(out, (x, y), 2, cv.RGB( 155, 0, 25))


            #cv2.imwrite("frame%d.jpg" % count, np.asarray(canny[:,:]))
            #cv.ShowImage(   'canny'    , canny   )
            #cv.ShowImage(   'harris'   , harris  )
            #cv.ShowImage(   'sobel'    , sobel   )
            #cv.ShowImage(   'output'   , out   )

            if cv2.waitKey(1) == 27:
                break
            count += 1
            
            self.image = sobel
        return

class OpenCVWidget ( Widget ):
    opencv = ObjectProperty( VideoToFrames("/Users/Poyner/Movies/test_movie.mov") )

    def on_touch_down ( self, touch ):
        print "touch"
    

        img = Image.fromarray(np.asarray(self.opencv.image))
        data = img.getdata()

        sio = StringIO(img.tostring()).getvalue()

        texture = Texture.create(size=(img.size[0], img.size[1]))
        texture.blit_buffer(sio, colorfmt='bgr', bufferfmt='ubyte')


        with self.canvas:
            Rectangle(texture=texture, pos=(0,0), size=img.size)
        
        #print kivyImage(img.getdata())
        #i = kivyImage( cv.fromarray( (self.opencv.image)) )
        #print self.opencv.image

    def on_touch_move ( self, touch ):
        pass

class OpenCVApp ( App ):
    def build ( self ) :
        return OpenCVWidget()
if __name__ == '__main__':
    OpenCVApp().run()

