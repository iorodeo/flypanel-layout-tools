import json
import numpy as np
import matplotlib.pyplot as plt
from .config import Config 
from .convert import inch_to_mm

class RingLayout:
    """
    Layout creator for ring arenas. 
    """

    def __init__(self, config):
        """
        RingLayout class constructor

        Parameters
        ---------
        config : Path, str, or dict
                 Path/str specifying the location of the .toml configuration file for
                 the arena or a dict with the configration valus.
        """
        self.config = self.load_config(config)
        self.values = self.make_values()
        self.print_values()
        self.show()


    def make_values(self):
        """
        Create arena layout values for creating plots and placing pcb components.
        """

        # Extract parameters from config - convert so units are mm and rad
        num_panel = self.config['panel']['number']
        panel_width = self.to_mm(self.config['panel']['width'])
        panel_depth = self.to_mm(self.config['panel']['depth'])
        offset_angle = self.to_rad(self.config['panel']['offset_angle'])
        omitted_panels = self.config['panel']['omitted']
        installed_mask = [not (i in omitted_panels) for i in range(num_panel)]
        num_pins  = self.config['pins']['number']
        pin_pitch = self.to_mm(self.config['pins']['pitch'])

        # Total length of header pins
        pin_width = (num_pins - 1)*pin_pitch   

        # Angle subtended by one panel 
        subtended_angle = 2.0*np.pi/num_panel      

        # Radius of circle tangent to panel front
        radius_front = (0.5*panel_width)/np.tan(0.5*subtended_angle)

        # Radius of circle tanget to panel rear
        radius_back = radius_front + panel_depth

        # Array of angular positions
        angles = np.arange(num_panel)*subtended_angle + offset_angle
        angles = angles[installed_mask]

        # x,y coords of panel center front positions
        front_x = radius_front*np.cos(angles)
        front_y = radius_front*np.sin(angles)

        # x,y coord of panel center back positions
        back_x = radius_back*np.cos(angles)
        back_y = radius_back*np.sin(angles)

        # Get lines for front of panels
        lines_front = get_face_lines(front_x, front_y, angles, panel_width)
        lines_back  = get_face_lines(back_x, back_y, angles, panel_width)
        lines_left, lines_right = get_side_lines(lines_front, lines_back)

        values = {
                'panel': {
                    'number'    : num_panel,
                    'width'     : panel_width,
                    'depth'     : panel_depth,
                    'subtended' : subtended_angle,
                    'omitted'   : omitted_panels,
                    },
                'pins': {
                    'number'    : num_pins, 
                    'pitch'     : pin_pitch,
                    'width'     : pin_width,
                    },
                'installed'     : installed_mask,
                'radius_front'  : radius_front,
                'radius_back'   : radius_back,
                'angles'        : angles,
                'front_x'       : front_x,
                'front_y'       : front_y,
                'back_x'        : back_x, 
                'back_y'        : back_y, 
                'lines_front'   : lines_front, 
                'lines_back'    : lines_back, 
                'lines_left'    : lines_left, 
                'lines_right'   : lines_right, 
                }
        return values

    def print_values(self):
        print()
        print('layout parameters')
        print('-'*95)
        print(f"num_panel:          {self.values['panel']['number']}")
        print(f"panel_width:        {self.values['panel']['width']} (mm)")
        print(f"panel_depth:        {self.values['panel']['depth']} (mm)")
        print(f"subtended_angle:    {self.values['panel']['subtended']} (rad)")
        print(f"installed:          {self.values['installed']}")
        print(f"num_pins:           {self.values['pins']['number']}")
        print(f"pin_width:          {self.values['pins']['width']} (mm)")
        print(f"radius_front:       {self.values['radius_front']} (mm)")
        print(f"radius_back:        {self.values['radius_back']} (mm)")
        print()

    def show(self):
        # Get title string
        num_panel = self.values['panel']['number']
        num_installed = np.array(self.values['installed']).sum()
        title = f'{num_installed}-{num_panel} Ring Arena'

        # Create plot showing arena layout
        fig, ax = plt.subplots(1,1)
        lines_and_colors = [ 
                ('lines_front', 'b'),
                ('lines_back',  'k'),
                ('lines_left',  'k'),
                ('lines_right', 'k'),
                ]
        for name, color in lines_and_colors:
            for line in self.values[name]:
                plt.plot(*line, color)
        ax.grid(True)
        ax.set_xlabel('x (mm)')
        ax.set_ylabel('y (mm)')
        ax.axis('equal')
        ax.grid(True)
        ax.set_title(title)
        plt.show()


    def load_config(self, config):
        return config if isinstance(config, Config) else Config(filename=config)


    def to_mm(self, v):
        return v if self.config['units']['length'] == 'mm' else inch_to_mm(v) 


    def to_rad(self, v):
        return v if self.config['units']['angle'] == 'rad' else np.deg2rad(v)


# Utility functions
# -------------------------------------------------------------------------------

def get_face_lines(xvals, yvals, angles, width):
    """ 
    Get lines for panel front (or back) panel faces.

    Parameters
    ----------
    xvals  : ndarray 
             array of x-coord of panel face centers

    yvals  : ndarray 
             array of y-coord of panel face centers

    angles : ndarray
             array of panel angles (rad) around ring

    width  : float
             the width of a panel (mm)

    Returns
    -------

    lines : list
            list of line coordinates [(x0,x1), (y0, y1)] for
            each panel face. 

    """
    lines = []
    for x, y, ang in zip(xvals, yvals , angles + 0.5*np.pi):
        x0 = x - 0.5*width*np.cos(ang)
        y0 = y - 0.5*width*np.sin(ang)
        x1 = x + 0.5*width*np.cos(ang)
        y1 = y + 0.5*width*np.sin(ang)
        lines.append([(x0,x1), (y0,y1)])
    return lines


def get_side_lines(lines_front, lines_back):
    """
    Get lines for panel sides.

    Parameters
    ----------
    lines_front : list
                  list of lines for panels front faces [(x0,x1),(y0,y1)]

    lines_back  : list
                  list of lines for panel back faces [(x0,x0),(y0,y1)]

    Returns
    -------
    lines_left  : list
                  list of lines for panel left faces 

    lines_right : list of lines for panel right faces
                 
    """
    lines_left  = []
    lines_right = []
    for fline, bline in zip(lines_front, lines_back):
        fx, fy = fline
        bx, by = bline
        lines_left.append([
            (fx[0], bx[0]), 
            (fy[0], by[0]),
            ])
        lines_right.append([
            (fx[1], bx[1]), 
            (fy[1], by[1])
            ])
    return lines_left, lines_right

def get_pin_pos(xvals, yvals, angles, num_pins, pin_pitch):
    """
    Get panel pin positions

    Parameters 
    ----------
    xvals     : ndarray 
                array of x-coord of panel face centers

    yvals     : ndarray 
                array of y-coord of panel face centers

    angles    : ndarray
                array of panel angles (rad) around ring

    num_pins  : int 
                number of pins on panel header

    pin_pitch : float
                pitch/dist between header pins

    Returns
    -------


    """
    pass














