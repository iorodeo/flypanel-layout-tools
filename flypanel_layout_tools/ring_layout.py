import copy
import json
import pprint
import pcbnew
import numpy as np
import matplotlib.pyplot as plt
from .config import Config 
from .convert import inch_to_mm

class RingLayout:
    """
    Layout creator for ring arenas. 
    """

    PRINT_FLOAT_PREC = 4

    def __init__(self, config, plot=False):
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
        if plot:
            self.plot_arena()


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
        num_installed = np.array(installed_mask).sum()
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
        pin_positions, pin_centers = get_pin_pos(angles, num_pins, radius_pins, 
                pin_pitch, omitted_pins)

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
                'num_installed' : num_installed,
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
                'pin_positions' : pin_positions,
                'pin_centers'   : pin_centers,
                }
        return values


    def print_values(self):
        """ Prints a subset of values of arena config """
        prec = self.PRINT_FLOAT_PREC
        print()
        print('parameters')
        print('----------')
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


    def plot_arena(self):
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
        for pos in self.values['pin_positions']:
            plt.plot(*pos, '.k')

        ax.grid(True)
        ax.set_xlabel('x (mm)')
        ax.set_ylabel('y (mm)')
        ax.axis('equal')
        ax.grid(True)
        ax.set_title(title)
        plt.show()

    def place_components(self, filename):

        # Load and print pcb placement parameters
        pcb_params = self.get_pcb_params()
        self.print_pcb_params(filename, pcb_params)

        # Extract placement parameters
        pcb_cx = pcb_params['center_x']
        pcb_cy = pcb_params['center_y']
        ref_prefix = pcb_params['panel']['ref_prefix']
        ref_start = pcb_params['panel']['ref_start']
        num = self.values['num_installed']
        panel_ref_list = [f'{ref_prefix}{i}' for i in range(ref_start, ref_start+num)]

        # Load board and place components
        pcb = pcbnew.LoadBoard(filename)

        # Get relative positions from model panel

        for ind, panel_ref in enumerate(panel_ref_list):
            footprint = pcb.FindFootprintByReference(panel_ref)
            angle = self.values['angles'][ind]
            cx, cy = self.values['pin_centers'][ind]
            cx, cy = cx + pcb_cx, cy + pcb_cy
            footprint.SetOrientationDegrees(np.rad2deg(-(angle - np.pi/2)))
            pos = pcbnew.VECTOR2I(pcbnew.FromMM(float(cx)),pcbnew.FromMM(float(cy)))
            footprint.SetPosition(pos)

        pcb.Save('test.kicad_pcb')
            

        



    def get_pcb_params(self):
        pcb_params = copy.deepcopy(self.config['pcb'])
        pcb_params['center_x'] = self.to_mm(pcb_params['center_x'])
        pcb_params['center_y'] = self.to_mm(pcb_params['center_y'])
        return pcb_params

    def print_pcb_params(self, filename, pcb_params):
        prec = self.PRINT_FLOAT_PREC
        print(f'placing components')
        print(f'------------------')
        print(f'  pcb file:      {filename}')
        print(f'  center x:      {pcb_params["center_x"]:0.{prec}f}')
        print(f'  center y:      {pcb_params["center_y"]:0.{prec}f}')
        print(f'  panel')
        print(f'    ref_prefix:  {pcb_params["panel"]["ref_prefix"]}')
        print(f'    ref_start:   {pcb_params["panel"]["ref_start"]}')
        print(f'  relative')   
        print(f'    model:       {pcb_params["relative"]["model"]}')


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

    pin_posittions : list 
                     list of pin positions for each header

    pin centers    : list 
                     list of pin center x,y coords for each header


    """
    pin_positions = [] 
    pin_centers = [] 
    width = (num - 1)*pitch   
    for ind, ang in enumerate(angles):
        cx = radius*np.cos(ang)
        cy = radius*np.sin(ang)
        pin_centers.append((cx, cy))
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
        pin_positions.append((pin_pos_x, pin_pos_y))
    return pin_positions, pin_centers


















