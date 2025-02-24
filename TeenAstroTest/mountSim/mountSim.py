import math, time, sys, argparse, csv
import numpy as np  
import trimesh
import trimesh.viewer
import glooey
import trimesh.transformations as tt
import pyglet
from pyglet import clock
from teenastro import TeenAstro, deg2dms

class Mount:
    def __init__(self, ta):

        self.mountType = ta.readMountType()     # one-letter code returned by TeenAstro 

        # Read the 3 parts that compose each type of mount
        if (self.mountType == 'E'):             # Equatorial German (GEM)
            self.base = trimesh.load('eq_german/base.stl')
            self.primary = trimesh.load('eq_german/primary.stl')
            self.secondary = trimesh.load('eq_german/secondary.stl')
        elif (self.mountType == 'K'):           # Equatorial Fork
            self.base = trimesh.load('eq_fork/base.stl')
            self.primary = trimesh.load('eq_fork/primary.stl')
            self.secondary = trimesh.load('eq_fork/secondary.stl')
        elif (self.mountType == 'A'):           # Altaz Tee
            self.base = trimesh.load('altaz_tee/base.stl')
            self.primary = trimesh.load('altaz_tee/primary.stl')
            self.secondary = trimesh.load('altaz_tee/secondary.stl')
        elif (self.mountType == 'k'):           # Altaz Fork
            self.base = trimesh.load('altaz_fork/base.stl')
            self.primary = trimesh.load('altaz_fork/primary.stl')
            self.secondary = trimesh.load('altaz_fork/secondary.stl')

        self.base.visual.face_colors = [100, 100, 100, 255]
        self.primary.visual.face_colors = [0, 0, 100, 255]
        self.secondary.visual.face_colors = [255, 0, 0, 255]

        # Read parameters from TeenAstro
        ta.readGears()
        self.axis1Degrees = ta.getAxis1()
        self.axis2Degrees = ta.getAxis2()
        self.alpha = self.beta = 0
        self.latitude = ta.getLatitude()

    def update(self, ta, scene):
        xaxis, yaxis, zaxis = [1,0,0],[0,1,0],[0,0,1]
        a1 = ta.getAxis1()
        a2 = ta.getAxis2()
        if (a1 == None) or (a2 == None):
            print("Connection Error")
            sys.exit(1)

        az = ta.getAzimuth()
        alt = ta.getAltitude()

# The transformations from axis positions (reported by TeenAstro) and rotations of the model
# Need to take into account both the hemisphere and the motor configurations
        if (a1 != self.axis1Degrees):
            if ta.axis1Reverse != (self.latitude>0):
                dir = 1
            else:
                dir = -1
            self.alpha = self.alpha + dir * np.deg2rad(self.axis1Degrees-a1)
            self.axis1Degrees = a1

        if (a2 != self.axis2Degrees):
            if ta.axis2Reverse:
                self.beta = self.beta + np.deg2rad(self.axis2Degrees-a2)
            else:
                self.beta = self.beta - np.deg2rad(self.axis2Degrees-a2)
            self.axis2Degrees = a2

# The clumsy code below represents the transformations required on the parts of each mount 
# so that they display properly. This is because I do not master completely the CAD program I used (SolveSpace)
# and it was quicker to do this than to properly align the parts in SolveSpace
        if (self.mountType == 'E'):             # Equatorial German (GEM)
            Mb1 = tt.rotation_matrix(np.deg2rad(90), yaxis)
            Mb2 = tt.rotation_matrix(np.deg2rad(-90), xaxis)
            Mb = tt.concatenate_matrices(Mb1, Mb2)
            Mp1 = tt.translation_matrix([-17,38,0])
            Mp2 = tt.rotation_matrix(np.deg2rad(90), yaxis)      
            Mp3 = tt.rotation_matrix(np.deg2rad(abs(self.latitude)-90), xaxis)      
            Mp4 = tt.rotation_matrix(self.alpha, yaxis)
            Mp = tt.concatenate_matrices(Mp1, Mp2, Mp3, Mp4)
            Ms1 = tt.rotation_matrix(np.deg2rad(90), xaxis)
            Ms2 = tt.translation_matrix([0,30,0])
            Ms3 = tt.rotation_matrix(-self.beta, yaxis)
            Ms = tt.concatenate_matrices(Mp,Ms1,Ms2,Ms3)

        elif (self.mountType == 'K'):           # Equatorial Fork
            Mb1 = tt.rotation_matrix(np.deg2rad(90), yaxis)
            Mb2 = tt.rotation_matrix(np.deg2rad(-90), xaxis)
            Mb = tt.concatenate_matrices(Mb1, Mb2)
            Mp1 = tt.translation_matrix([0,60,0])
            Mp2 = tt.rotation_matrix(np.deg2rad(-90), xaxis)      
            Mp3 = tt.rotation_matrix(np.deg2rad(abs(self.latitude)-90), yaxis)      
            Mp4 = tt.rotation_matrix(self.alpha, zaxis)
            Mp = tt.concatenate_matrices(Mp1, Mp2, Mp3, Mp4)
            Ms1 = tt.rotation_matrix(np.deg2rad(90), yaxis)
            Ms2 = tt.translation_matrix([-90, 0, 0])
            Ms3 = tt.rotation_matrix(-self.beta, yaxis)
            Ms = tt.concatenate_matrices(Mp,Ms1,Ms2,Ms3)

        elif (self.mountType == 'A'):           # Altaz Tee
            Mb = tt.rotation_matrix(0, xaxis)    
            Mp1 = tt.rotation_matrix(self.alpha, zaxis)
            Mp2 = tt.translation_matrix([0, 0, 80])
            Mp = tt.concatenate_matrices(Mp1,Mp2)
            Ms1 = tt.translation_matrix([20, 0, 16])
            Ms2 = tt.rotation_matrix(-self.beta, xaxis)
            Ms = tt.concatenate_matrices(Mp,Ms1,Ms2)

        elif (self.mountType == 'k'):           # Altaz Fork
            Mb = tt.rotation_matrix(np.deg2rad(180), yaxis)     
            Mp = tt.rotation_matrix(self.alpha, yaxis)
            Ms1 = tt.translation_matrix([0,56,0])
            Ms2 = tt.rotation_matrix(self.beta, zaxis)
            Ms = tt.concatenate_matrices(Mp,Ms1,Ms2)
        
        base = scene.graph.nodes_geometry[0]
        primary = scene.graph.nodes_geometry[1]
        secondary = scene.graph.nodes_geometry[2]

        # apply the transform to the node
        scene.graph.update(base, matrix=Mb)
        scene.graph.update(primary, matrix=Mp)
        scene.graph.update(secondary, matrix=Ms)

        # return the axis positions for logging
        return [a1,a2,az,alt]



# Declare function to define command-line arguments
def readOptions(args=sys.argv[1:]):
  parser = argparse.ArgumentParser(description="The parsing commands lists.")
  parser.add_argument('-p', '--ip', help='TeenAstro IP address')
  opts = parser.parse_args(args)
  if opts.ip == None:
    opts.ip = '192.168.0.21'
  return opts

testCase = [{'name':'South','az':180,'alt':0}, {'name':'East','az':90,'alt':0},{'name':'North','az':0,'alt':0},{'name':'West','az':270,'alt':0}]
#testCase = [{'name':'South','az':180,'alt':0}, {'name':'East','az':90,'alt':0}]


# Main program
class Application:

    def __init__(self, options):

        self.width, self.height = 800, 600
        window = self._create_window(width=self.width, height=self.height)

        gui = glooey.Gui(window)
        hbox = glooey.HBox()

        self.ta = self.init_TeenAstro(options.ip)
        if self.ta == None:
            self.log ("Error connecting to TeenAstro")
            sys.exit(1)

        self.log('Connected')

        self.mount = Mount(self.ta)
        self.testData = []

        scene = trimesh.Scene([self.mount.base, self.mount.primary, self.mount.secondary])
        self.scene_widget1 = trimesh.viewer.SceneWidget(scene)
        self.update(0)
        hbox.add(self.scene_widget1)

        # text box - not yet implemented
#        self.textWidget = glooey.Label('hello')
#        hbox.add(self.textWidget)
        vbox = glooey.VBox()
        hbox.add(vbox)

        button = glooey.Button("Meridian Flip Test")
        button.push_handlers(on_click=self.startFlipTest)
        vbox.add(button)

        button = glooey.Button("Coordinates Test")
        button.push_handlers(on_click=self.startCoordTest)
        vbox.add(button)

        if self.mount.mountType == 'E':
            self.log('German Equatorial')
        elif self.mount.mountType == 'K':
            self.log('Equatorial Fork')
        elif self.mount.mountType == 'k':
            self.log('Alt-Az Fork')
        elif self.mount.mountType == 'A':
            self.log('Alt-Az Tee')

        self.log('Latitude:'+str(self.ta.getLatitude()))

        gui.add(hbox)
        pyglet.clock.schedule_interval(self.update, 1. / 5) 
        pyglet.app.run()

    def startFlipTest(self, dt):
        if self.mount.mountType != 'E':
            self.log('Can only run meridian flip test with German Equatorial mount')
            return
        self.log('Starting meridian flip test')
        if not self.ta.isAtHome():
            self.log('Error - mount is not at home')
            return

        self.flipTestState = 'start'
        pyglet.clock.schedule_interval(self.runFlipTest, 0.5) 

    def runFlipTest(self, dt):
        if self.ta.isSlewing():
            return

        code = self.ta.getErrorCode()
        if code!= 'ERR_NONE':
            self.log(code)
            pyglet.clock.unschedule(self.runFlipTest) 
            return

        if self.flipTestState == 'start':
            self.eastLimit = self.ta.getMeridianEastLimit()
            self.westLimit = self.ta.getMeridianWestLimit()

            self.initialRA = self.ta.readSidTime() + (1.0 + float(self.eastLimit)) / 15.0 # goto "eastLimit" east of south meridian  
            self.initialDec = 0
            self.ta.gotoRaDec(self.initialRA, self.initialDec)
            self.log('goto East Limit')
            self.flipTestState = 'goto1'
            return

        if self.flipTestState == 'goto1':
            self.ra = self.ta.getRA() - (0.04 + float(self.eastLimit + self.westLimit) / 15)  # go almost to west limit 
            self.dec = self.ta.getDeclination()
            self.log('goto West Limit')
            self.ta.gotoRaDec(self.ra, self.dec)
            self.flipTestState = 'goto2'
            self.t = self.startWaiting = time.time()

        if self.flipTestState == 'goto2':
            if (self.ta.getPierSide() == 'W'):    # still on west side. wait 5 seconds and issue a goto to the same position
                t = time.time()
                if (t < self.t + 5):
                    return
                self.t = t
                print('.')
                t = time.time()
                self.ta.gotoRaDec(self.ra, self.dec)

            else:           # we have flipped - test is done
                self.log('meridian flip done after %d seconds - goto Home' % (self.t - self.startWaiting))
                self.ta.goHome()
                pyglet.clock.unschedule(self.runFlipTest) 

    def startCoordTest(self,arg):
        self.testStep = 0
        self.testData = []
        pyglet.clock.schedule_interval(self.runCoordTest, 0.5) 

    def runCoordTest(self, dt):
        if self.ta.isSlewing():
            return

        if self.testStep == len(testCase):
            self.log ('done - go Home')
            self.ta.goHome()
            pyglet.clock.unschedule(self.runCoordTest) 
            fields = ['axis1', 'axis2', 'azimuth', 'altitude']
            with open('mountSim.csv', 'w') as f:
                write = csv.writer(f)
                write.writerow(fields)
                write.writerows(self.testData)            
            return

        self.log ('goto ' + testCase[self.testStep]['name'])
        res = self.ta.gotoAzAlt(testCase[self.testStep]['az'],testCase[self.testStep]['alt'])
        if (res):
            self.log(res)
        self.testStep = self.testStep + 1


    # May override this with a graphical window in the future
    def log(self, message):
        print (message)

    def init_TeenAstro(self, ip):
        ta = TeenAstro('tcp', ip)
        p = ta.open()

        if (p == None):
          self.log ('Error connecting to TeenAstro')
          sys.exit()
        return ta

    def update(self, dt):
        axisPos = self.mount.update(self.ta, self.scene_widget1.scene)
        self.testData.append(axisPos)
        self.scene_widget1._draw()

    def _create_window(self, width, height):
        try:
            config = pyglet.gl.Config(sample_buffers=1,
                                      samples=4,
                                      depth_size=24,
                                      double_buffer=True)
            window = pyglet.window.Window(config=config,
                                          width=width,
                                          height=height)
        except pyglet.window.NoSuchConfigException:
            config = pyglet.gl.Config(double_buffer=True)
            window = pyglet.window.Window(config=config,
                                          width=width,
                                          height=height)

        @window.event
        def on_key_press(symbol, modifiers):
            if modifiers == 0:
                if symbol == pyglet.window.key.Q:
                    window.close()
        return window

 
if __name__ == '__main__':
    options = readOptions()
    Application(options)
