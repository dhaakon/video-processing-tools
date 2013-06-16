'''
    OpenCV Video Helper class. Manages the playback, processing, encoding, and 
    decoding of video files. Currently .mp4 files work best.

    Video class generates a kivy texture using :StringIO: (note: not the most 
    performant).
'''

import cv
import cv2

BLUR_SIZE    = 3

class OCVVideo(object):
    def __init__ ( self, effect, size ):
        self.effect         =   effect          #   The effect
        self.total_frames   =   0               #   Total frames
        self.framerate      =   0               #   Framerate (Best of OCV's abilities ** Lot's of bugs **
        self.duration       =   0               #   Duration
        self.milliseconds   =   0               #   in Milliseconds
        self.SCALE          =   1               #   it's Scale
        self.vidcap         =   None            #   VideoCapture
        self.cvMat          =   None            #   The open CV matrix
        self.output         =   None            #   output
        self.isWebCam       =   True            #   is it a webcam feed?
        self.video_size     =   size

    def seek (self, frame_int):
        cv.SetCaptureProperty(self.vidcap, cv.CV_CAP_PROP_POS_MSEC, frame_int)

    def get_total_time(self):
        '''
            Grab the properties for the video
        '''

        self.total_frames   =   float(cv.GetCaptureProperty( self.vidcap, cv.CV_CAP_PROP_FRAME_COUNT) )
        self.framerate      =   float(cv.GetCaptureProperty( self.vidcap,cv.CV_CAP_PROP_FPS) )
        self.duration       =   self.total_frames / self.framerate
        self.milliseconds   =   self.duration * 1000

    def create_video_capture ( self, path ):
        '''
            Create an OpenCV video capture. Currently unencoding .mp4 directly 
            from the go pro works best for :seek:
        '''
        if self.vidcap != None:
            print 'releasing video'
            self.vidcap.release()

        #self.vidcap = cv.CaptureFromFile( path )
        if self.isWebCam == True:
            self.vidcap = cv.CaptureFromCAM( 0 )
            cv.SetCaptureProperty( self.vidcap, cv.CV_CAP_PROP_FRAME_WIDTH, self.video_size[0])
            cv.SetCaptureProperty( self.vidcap, cv.CV_CAP_PROP_FRAME_HEIGHT, self.video_size[1])
        else:
            self.vidcap = cv.CaptureFromFile( path )
            self.prevImage = cv.QueryFrame(self.vidcap)
            #self.get_total_time()

    def set_video_capture(self, vidcap):
        pass

    def get_current_time_in_mill ( self ):
        '''
            Get the current time in milliseconds
        '''
        return cv.GetCaptureProperty(self.vidcap, cv.CV_CAP_PROP_POS_MSEC)

    def get_completion_percentage(self):
        '''
            Return the percent complete for the video
        '''
        return self.get_current_time_in_mill() / self.milliseconds

    def grab_image ( self, count, texture_type ):
        '''
            Return the next frame in the video
        '''
        #self.seek(count)
        image = cv.QueryFrame(self.vidcap)

        return True, self.process_image(image, texture_type)

    def process_image( self, image, texture_type ):
        '''
            To be overridden to represent effect
        '''
        return image
        pass

    def add_OCV_Effect( self, effect ):
        pass

    def chain_effects ( self, effects ):
        pass

    def get_cv_mat ( self, mat ):
        return cv.fromarray(mat)


class Canny       (OCVVideo):
    def __init__(self, effect):
        super(Canny, self).__init__(effect)


class SobelViewer (OCVVideo):
    def __init__(self, effect, size):
        super(SobelViewer, self).__init__(effect, size)

    def create_sobel(self, image):
        pass

    def set_channel(self, image):
        pass

    def get_channel(self, image):
        pass

    def get_garbage_image(self, image):
        pass
        
    def process_image(self, image, texture_type):
        spare = image
        #return image
        # get the size of the current image
        size = ( image.width, image.height )
        
        cv.Smooth( spare, spare, cv.CV_GAUSSIAN, BLUR_SIZE, BLUR_SIZE )

        #out = cv.CreateImage( size, 8, 1)
        cannyB  = cv.CreateImage( size , 8, 1 )
        cannyR  = cv.CreateImage( size , 8, 1 )
        sobel  = cv.CreateImage( size , 8, 1 )
        yuv    = cv.CreateImage( size , 8, 3 )
        dest_canny   = cv.CreateImage( size , 8, 3 )
        gray   = cv.CreateImage( size , 8, 1 )

        cv.CvtColor( spare, yuv, cv.CV_BGR2YCrCb )
        cv.Split( yuv, gray, None, None, None)
        
        cv.Canny( gray, cannyB, 5, 50, 3)
        cv.Canny( gray, cannyR, 5, 150, 3)
        cv.Sobel( gray, sobel, 1, 0, 3 )

        #cv.ConvertScale(sobel, sobel, -1, 255 )
        #cv.ConvertScale(cannyR, cannyR, -1, 155 )
        #cv.ConvertScale(gray, gray, -1, 255 )
        #cv.ConvertScale(cannyB, cannyB, -1, 255 )

        cv.Smooth( cannyR, cannyR, cv.CV_GAUSSIAN, 3, 3 )
        cv.Smooth( cannyB, cannyB, cv.CV_GAUSSIAN, 3, 3 )
        #cv.CvtColor( canny, canny, cv.CV_YCrCb2BGR )
        #cv.Merge(sobel, gray, sobel, None, dest)
        cv.Merge(cannyR,cannyB, gray, None, dest_canny)

        #cv.Merge(sobel, sobel, sobel, None, dest_sobel)
        #cv.Smooth( dest, dest, cv.CV_GAUSSIAN, BLUR_SIZE, BLUR_SIZE )
        #cv.ShowImage( 'canny', dest)

        #cv.Merge
        #cv.Smooth( dest_canny, dest_canny, cv.CV_GAUSSIAN, BLUR_SIZE, BLUR_SIZE )

        #success = True
        self.prevImage = image

        options = {
            'normal':dest_canny,
            'post':dest_canny
        }
        #return yuv 
        return options[texture_type] 



