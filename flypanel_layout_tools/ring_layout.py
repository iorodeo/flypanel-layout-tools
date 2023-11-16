import json
import pprint
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
                 Path/str specifying the location of the .toml configuration 
                 file for the arena or a dict with the configration values.
        """
        self.config = self.load_config(config)
        self.values = self.make_values()
        self.print_values()
        self.show()


    def make_values(self):
        """
        Creates the arena layout values for creating plots and placing pcb
        components.
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
        pin_depth = self.to_mm(self.config['pins']['depth'])
        omitted_pins = self.config['pins']['omitted']

        # Angle subtended by one panel 
        subtended_angle = 2.0*np.pi/num_panel      

        # Radius of circle tangent to panel front
        radius_front = (0.5*panel_width)/np.tan(0.5*subtended_angle)

        # Radius of circle tangent to panel rear
        radius_back = radius_front + panel_depth

        # Radius of circle tangent to line of panel pins
        radius_pins = radius_front + pin_depth

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

        # Get pin positions
        pin_pos = get_pin_pos(angles, num_pins, radius_pins, pin_pitch, omitted_pins)

        values = {
                'panel': {
                    'number'       : num_panel,
                    'width'        : panel_width,
                    'depth'        : panel_depth,
                    'subtended'    : subtended_angle,
                    'omitted'      : omitted_panels,
                    'offset_angle' : offset_angle,
                    },
                'pins': {
                    'number'    : num_pins, 
                    'pitch'     : pin_pitch,
                    'omitted'   : omitted_pins,
                    },
                'installed'     : installed_mask,
                'radius_front'  : radius_front,
                'radius_back'   : radius_back,
                'radius_pins'   : radius_pins,
                'angles'        : angles,
                'front_x'       : front_x,
                'front_y'       : front_y,
                'back_x'        : back_x, 
                'back_y'        : back_y, 
                'lines_front'   : lines_front, 
                'lines_back'    : lines_back, 
                'lines_left'    : lines_left, 
                'lines_right'   : lines_right, 
                'pin_pos'       : pin_pos,
                }
        return values


    def print_values(self):
        """ Prints a subset of values of arena config """
        prec = 4
        print()
        print('layout parameters')
        print('-'*90)
        print(f'panel')
        print(f'  number:        {self.values["panel"]["number"]}')
        print(f'  width:         {self.values["panel"]["width"]:0.{prec}f} (mm)')
        print(f'  depth:         {self.values["panel"]["depth"]:0.{prec}f} (mm)')
        print(f'  subtended:     {self.values["panel"]["subtended"]:0.{prec}f} (rad)')
        print(f'  omitted:       {self.values["panel"]["omitted"]}')
        print(f'  offset angle:  {self.values["panel"]["offset_angle"]:0.{prec}f} (rad)')
        print(f'pins')
        print(f'  number:        {self.values["pins"]["number"]}')
        print(f'  pitch:         {self.values["pins"]["pitch"]:0.{prec}f} (mm)')
        print(f'  width:         {self.values["pins"]["pitch"]:0.{prec}f} (mm)')
        print(f'radius_front:    {self.values["radius_front"]:0.{prec}f} (mm)')
        print(f'radius_pins:     {self.values["radius_pins"]:0.{prec}f} (mm)')
        print(f'radius_back:     {self.values["radius_back"]:0.{prec}f} (mm)')
        #print(f'installed:       {self.values["installed"]}')
        print()


    def show(self):
        """ Plots a figure of showing the arena layout geometry """
        # Get title string
        num_panel = self.values['panel']['number']
        num_installed = np.array(self.values['installed']).sum()
        title = f'{num_installed}-{num_panel} Ring Arena'

        # Create plot showing arena layout
        fig, ax = plt.subplots(1,1)
        lines_and_colors = [ 
                ('lines_front', 'g'),
                ('lines_back',  'b'),
                ('lines_left',  'b'),
                ('lines_right', 'b'),
                ]

        # Plot panel sides 
        for name, color in lines_and_colors:
            for line in self.values[name]:
                plt.plot(*line, color)

        # Plot panel pins
        for _, pos in self.values['pin_pos'].items():
            plt.plot(*pos, '.k')

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

def get_pin_pos(angles, num, radius, pitch, omitted):
    """
    Get panel pin positions

    Parameters 
    ----------
    angles  : ndarray
              array of panel angles (rad) around ring

    num     : int 
              number of pins on panel header

    radius  : float
              radius of circle tangent to line of panel pins

    pitch   : float
              pitch/dist between header pins

    omitted : list of omitted pins

    Returns
    -------


    """
    ind_to_pin_pos = {}
    width = (num - 1)*pitch   
    for ind, ang in enumerate(angles):
        cx = radius*np.cos(ang)
        cy = radius*np.sin(ang)
        pin_pos_x = []
        pin_pos_y = []
        for i in range(num):
            if (i+1) in omitted:
                continue
            d  = i*pitch
            x = cx + (i*pitch - 0.5*width)*np.cos(ang + 0.5*np.pi)
            y = cy + (i*pitch - 0.5*width)*np.sin(ang + 0.5*np.pi)
            pin_pos_x.append(x)
            pin_pos_y.append(y)
        ind_to_pin_pos[ind] = (pin_pos_x, pin_pos_y)
    return ind_to_pin_pos


















