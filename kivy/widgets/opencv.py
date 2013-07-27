'''
    OpenCV Video Helper class. Manages the playback, processing, encoding, and 
    decoding of video files. Currently .mp4 files work best.

    Video class generates a kivy texture using :StringIO: (note: not the most 
    performant).
'''

import cv
import cv2
import numpy as np
import time
import sys, os, random, hashlib
from scipy import *
from scipy.cluster import vq

from math import *


BLUR_SIZE    = 3
def merge_collided_bboxes( bbox_list ):
	# For every bbox...
	for this_bbox in bbox_list:

		# Collision detect every other bbox:
		for other_bbox in bbox_list:
			if this_bbox is other_bbox: continue  # Skip self

			# Assume a collision to start out with:
			has_collision = True

			# These coords are in screen coords, so > means 
			# "lower than" and "further right than".  And < 
			# means "higher than" and "further left than".

			# We also inflate the box size by 10% to deal with
			# fuzziness in the data.  (Without this, there are many times a bbox
			# is short of overlap by just one or two pixels.)
			if (this_bbox[bottom][0]*1.1 < other_bbox[top][0]*0.9): has_collision = False
			if (this_bbox[top][0]*.9 > other_bbox[bottom][0]*1.1): has_collision = False

			if (this_bbox[right][1]*1.1 < other_bbox[left][1]*0.9): has_collision = False
			if (this_bbox[left][1]*0.9 > other_bbox[right][1]*1.1): has_collision = False

			if has_collision:
				# merge these two bboxes into one, then start over:
				top_left_x = min( this_bbox[left][0], other_bbox[left][0] )
				top_left_y = min( this_bbox[left][1], other_bbox[left][1] )
				bottom_right_x = max( this_bbox[right][0], other_bbox[right][0] )
				bottom_right_y = max( this_bbox[right][1], other_bbox[right][1] )

				new_bbox = ( (top_left_x, top_left_y), (bottom_right_x, bottom_right_y) )

				bbox_list.remove( this_bbox )
				bbox_list.remove( other_bbox )
				bbox_list.append( new_bbox )

				# Start over with the new list:
				return merge_collided_bboxes( bbox_list )

	# When there are no collions between boxes, return that list:
	return bbox_list

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
        self.frame_count    =   0
        self.show_frame = False

        # Blob tracking settings
        self.target_count = 1
        self.last_target_count = 1
        self.last_target_change_t = 0.0
        self.k_or_guess = 1
        self.codebook = []
        self.frame_count = 0
        self.last_frame_entity_list = []

        self.t0 = time.time()
        self.frame_t0 = None
        self.top = 0
        self.bottom = 1
        self.left = 0
        self.right = 1

        self.storage = cv.CreateMemStorage(0)
        self.cx = 0
        self.cy = 0

        self.min_hue = 5
        self.min_sat = 112
        self.min_val = 55

        self.max_hue = 45
        self.max_sat = 255
        self.max_val = 255
        
        self.value_dict = {
            'min_hue' : self.min_hue,
            'max_hue' : self.max_hue,
            'min_sat' : self.min_sat,
            'max_sat' : self.max_sat,
            'min_val' : self.min_val,
            'max_val' : self.max_val

        }
    
        self.max_targets = 3


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
        self.frame_count += 1
        return True, self.process_image(image, texture_type)

    def process_image( self, image, texture_type ):
        '''
            To be overridden to represent effect
        '''

        if type(image) != None:
            return self.track_blobs( image )
            #return self.track_blobs2( image )
        pass

    def add_OCV_Effect( self, effect ):
        pass

    def chain_effects ( self, effects ):
        pass

    def get_cv_mat ( self, mat ):
        return cv.fromarray( mat )
    '''
        http://stackoverflow.com/questions/12943410/opencv-python-single-rather-than-multiple-blob-tracking?answertab=active#tab-self.top
    '''
    def get_value ( self, value_type ):
        return self.value_dict[value_type]

    def set_value (self, value_type, value):
        self.value_dict[value_type] = int(value)
        print value_type, self.min_hue
        value = int(value)

        if value_type is "min_hue":
            print value
            self.min_hue = value
        elif value_type is "max_hue":
            self.max_hue = value
        elif value_type is "min_sat":
            self.min_sat = value
        elif value_type is "max_sat":
            self.max_sat = value
        elif value_type is "min_val":
            self.min_val = value
        elif value_type is "max_val":
            self.max_val = value

            
        #print int(value)
        #print self.value_dict[value_type]

    def track_blobs ( self, frame ):
        spare = cv.CloneImage(frame)
        size = cv.GetSize(frame)

        hsv = cv.CreateImage( size, cv.IPL_DEPTH_8U, 3)
        out = cv.CreateImage( size, cv.IPL_DEPTH_8U, 3)
        thresh = cv.CreateImage( size, cv.IPL_DEPTH_8U, 1)

        print self.min_hue, self.value_dict['min_hue']


        cv.Smooth( spare, spare, cv.CV_BLUR, 22, 22)
        cv.CvtColor( spare, hsv, cv.CV_BGR2HSV )

        cv.InRangeS( hsv, 
                     cv.Scalar( self.min_hue, self.min_sat, self.min_val ), 
                     cv.Scalar( self.max_hue, self.max_sat, self.max_val ), 
                     thresh )

        cv.Merge( thresh, thresh, thresh, None, out )
        contours = cv.FindContours(  thresh,
                                     self.storage,
                                     cv.CV_RETR_LIST,
                                     cv.CV_CHAIN_APPROX_SIMPLE )

        try:
            M = cv.Moments( contours )
        except:
            return out 

        m0 = cv.GetCentralMoment( M, 0, 0)

        if m0 > 1.0:
            self.cx = cv.GetSpatialMoment( M, 1, 0) / m0
            self.cy = cv.GetSpatialMoment( M, 0, 1) / m0
            cv.Circle( frame, (int(self.cx), int(self.cy)), 2, (255,0,0), 20)
        if self.show_frame is not True:
            return out
        else:
            return frame

        pass


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



