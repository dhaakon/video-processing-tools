import sys
sys.path.append('/Users/Poyner/Development/video-processing-tools/kivy/widgets/')
sys.path.append('/Users/Poyner/Development/video-processing-tools/kivy/shaders/')

import kivy
import kivy.input.providers.mactouch
from kivy.graphics.gl_instructions import *

kivy.require('1.7.1')

'''
    WINDOW SETTINGS
'''

# Default size for the window and video
SIZE = [ 1280, 720 ]

from kivy.config import Config

Config.set( 'graphics',  'width', SIZE[0] )
Config.set( 'graphics', 'height', SIZE[1] )

from kivy.base import EventLoop
from kivy.app import App

from kivy.animation import *

from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Rectangle, RenderContext, Fbo
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.uix.button import Button
from kivy.graphics.context_instructions import *

from kivy.graphics.texture import Texture

from opencv import *
from opencvviewer import *

from kivy.uix.widget import Widget

from kivy.clock import Clock
from kivy.core.window import WindowBase

from shaders import Shaders

EventLoop.ensure_window()
path = ''

class OCVWindow(WindowBase):
    def __init__(self, **kwargs):
        super(OCVWindow, self).__init__(**kwargs)
        print self.width

'''
    Container widget
    ----------------

    Root widget which subsequent widgets inherit from
'''

class OCVBackground (FloatLayout):
    def __init__(self, **kwargs):
        super(OCVBackground, self).__init__(**kwargs)
    pass

class OCVHSVControls(StackLayout):
    min_hsv     =   ObjectProperty(None)
    max_hsv     =   ObjectProperty(None)
    min_sat     =   ObjectProperty(None)
    max_sat     =   ObjectProperty(None)
    min_val     =   ObjectProperty(None)
    max_val     =   ObjectProperty(None)

    def __init__(self, **kwargs):
        super(OCVHSVControls, self).__init__(**kwargs)

    pass
    def check_box_handler(self, value):
        self.ocv_viewer.ocv_video.show_frame = value
    def slider_changed(self, value_type, value):
        
        self.ocv_viewer.set_value(value_type, value.value)

class OCVViewer (Widget):
    texture=ObjectProperty(None)
    state=NumericProperty(None)

    def __init__(self, ocv_property, **kwargs):
        super(OCVViewer, self).__init__(**kwargs)
        self.ocv_video = OCVVideo('post', SIZE)
        self.path = ''

        self.ocv_video.create_video_capture( self.path )

        self.texture = Texture.create(size=(SIZE))
        self.texture.flip_vertical()
        self.state = 0

    def get_value( self, value_type ):
        return self.ocv_video.get_value(value_type)

    def set_value( self, value_type, value ):
        self.ocv_video.set_value(value_type, value)


    '''
        Send the texture to the parent canvas
    '''

    def load_texture ( self, texture, pos, name ):
        with self.post_effect.fbo:
            ClearBuffers()
            ClearColor(0, 0, 0, 0)

        self.post_effect.texture0.texture = texture
        #self.post_effect.save(name) 
    '''
        on_touch_move
        Seeks to the frame based on the ratio of touchX to widget.width
    '''

    def on_touch_move(self, touch):
        if self.ocv_video.isWebCam == True:
            return

        curr_time = self.ocv_video.get_current_time_in_mill()

        if touch.dsx > 0.03 or touch.dsx < -0.03:
            diff_x = (touch.pos[0] / SIZE[0]) * self.ocv_video.ocv.milliseconds
            diff_y = (touch.dy * 10)
        else:
            diff_x = 0
            diff_y = (touch.dy * 10) + curr_time

        succss, post_image = self.ocv_video.grab_image(diff_x + diff_y, "post" )
        self.convert_image_to_texture( post_image, self.texture )
        self.post_effect.update_glsl()

    '''
        on_touch_down
    increment the state to detect multiple touches
    '''

    def on_touch_down(self, touch):
        self.state += 1
    '''
        on_touch_move
        decrease state by 1
    '''

    def on_touch_up(self, touch):
        self.state -= 1
    pass

    '''
        Helper class which converts cv2 mat into a kivy texture. Currently more 
        performant to feed texture
    '''

    def convert_image_to_texture ( self, image, texture ):
        texture.blit_buffer(image.tostring(), colorfmt='bgr', bufferfmt='ubyte')
        return texture
    '''
        Grabs the frame from the OCV Video then updates the shader
    '''
    def get_frame ( self, frameCount ):
        succss, post_image = self.ocv_video.grab_image(frameCount, "post" )
        self.convert_image_to_texture( post_image, self.texture )
        self.post_effect.update_mouse(self.ocv_video.cx, self.ocv_video.cy)
        self.post_effect.update_glsl()
        self.load_texture(self.texture, (0,0), 'e'+str(frameCount))


class PostEffect (Widget):
    fs=StringProperty(None)
    texture=ObjectProperty(None)
    mouse=ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PostEffect, self).__init__(**kwargs)
        self.canvas = RenderContext(use_parent_projection=True)
        self.fs = Shaders.shader_pulse
        self.mouse = (0,0)
        self.textures = []

        with self.canvas:
            self.fbo = Fbo(size=SIZE, use_parent_projection=True)
            self.texture0 = Rectangle(size=SIZE)
 
        self.texture = self.fbo.texture
        self.texture.flip_vertical()
    def update_mouse(self, cx, cy):
        """docstring for uo"""
        # TODO: write code...
        self.mouse = (cx, cy)

    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = map(float, self.size)
        self.canvas['mouse'] = map(float, self.mouse)
        #self.save(str(Clock.get_boottime()))

    def save(self, path):
        self.fbo.texture.save(path + '.jpg')

    def on_fs(self, instance, value):
        # set the fragment shader to our source code
        shader = self.canvas.shader
        old_value = shader.fs
        shader.fs = value

        if not shader.success:
            shader.fs = old_value
            raise Exception('failed')

    def on_touch_move(self, touch):
        pass
        #self.mouse = touch.pos
    # now, if we have new widget to add,
    # add their graphics canvas to our Framebuffer, not the usual canvas.
    #
    def add_texture(self, texture):
        self.textures.push(texture)
        idx = len(self.textures)

        with self.canvas:
            self['texture' + idx] = Rectangle(size=SIZE)
        pass

    def add_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(PostEffect, self).add_widget(widget)
        self.canvas = c

    def remove_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(PostEffect, self).remove_widget(widget)
        self.canvas = c

class OCVButtons (GridLayout):
    play_button     =   ObjectProperty(None)
    stop_button     =   ObjectProperty(None)

    ocv_viewer      =   ObjectProperty(None)
    count           =   NumericProperty(400000)
    fn              =   NumericProperty(0)

    '''
        Animation Properties
    '''

    fade_in=ObjectProperty(None)
    fade_out=ObjectProperty(None)

    duration=NumericProperty(0.2)

    def __init__ ( self, **kwargs ):
        super(OCVButtons, self).__init__(**kwargs)
        self.fade_in = Animation(opacity=1, duration=self.duration)
        self.fade_out = Animation(opacity=0, duration=self.duration)

    def my_callback ( self, dt ):
        if self.count < self.ocv_viewer.ocv_video.milliseconds:
            self.count += 50
        else:
            self.count = 0
        self.fn += 1
        self.ocv_viewer.get_frame(self.count)

    #Listeners 
    def button_pressed (self, text):
        def play( self ):
            self.ocv_viewer.get_frame(1)
            self.fade_in.start(self.stop_button)
            self.fade_out.start(self.play_button)
            Clock.schedule_interval(self.my_callback, 1/30) 

        def stop( self ):
            self.fade_out.start(self.stop_button)
            self.fade_in.start(self.play_button)

            Clock.unschedule(self.my_callback) 

        options = {
                "Play":play,
                "Stop":stop
        }

        options[text]( self )
    pass

class ChannelViewer(StackLayout):
    def __init__(self, **kwargs):
        super(ChannelViewer, self).__init__(**kwargs)
        pass

class VideoProcessingApp(App): 
    def build ( self ) :
        # Set our container
        self.app = OCVBackground()

        # UI element
        buttons = OCVButtons()
        self.ocv_hsv_controls = OCVHSVControls()
        self.ocv_hsv_controls.ocv_viewer = self.ocv_viewer = buttons.ocv_viewer = OCVViewer("post")
        buttons.post_effect = self.ocv_viewer.post_effect = self.post_effect = PostEffect()

        self.ocv_viewer.get_frame(1)
        self.app.add_widget(self.post_effect)
        self.post_effect.add_widget(self.ocv_viewer)


        self.app.add_widget(buttons)
        self.app.add_widget(self.ocv_hsv_controls)
        buttons.button_pressed("Play")

        return self.app

if __name__ == '__main__':
    VideoProcessingApp().run()

