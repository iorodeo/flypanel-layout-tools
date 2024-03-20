import pcbnew
import collections
import numpy as np
import matplotlib.pyplot as plt
from .config import Config 
from .convert import inch_to_mm
from .convert import pos_to_pcbnew_vec 

class LedArray:

    def __init__(self, config, plot=True):
        self.plot = True
        self.config = self.load_config(config)

    def place_components(self, filename):

        w_pcb = self.to_mm(self.config['pcb']['size_x'])
        h_pcb = self.to_mm(self.config['pcb']['size_y'])
        cx_pcb = self.to_mm(self.config['pcb']['center_x'])
        cy_pcb = self.to_mm(self.config['pcb']['center_y'])

        nrows = self.config['pcb']['led']['nrows']
        ncols = self.config['pcb']['led']['ncols']
        ref_prefix = self.config['pcb']['led']['ref_prefix']
        ref_start = self.config['pcb']['led']['ref_start']
        angle_led = self.to_rad(self.config['pcb']['led']['angle'])

        nleds = nrows*ncols
        dx_led = w_pcb/ncols   # LED x spacing
        dy_led = h_pcb/nrows   # LED y spacing
        w_led = (ncols-1)*dx_led   # width  of LED array
        h_led = (nrows-1)*dy_led   # height of LED array

        pcb = pcbnew.LoadBoard(filename)

        led_num = ref_start 
        for i in range(ncols):
            for j in range(nrows):
                ref = f'{ref_prefix}{led_num}'
                x_led = cx_pcb + i*dx_led - 0.5*w_led  
                y_led = cy_pcb + j*dy_led - 0.5*h_led
                pos = (x_led, y_led)

                footprint = pcb.FindFootprintByReference(ref)
                vec = pos_to_pcbnew_vec(pos)
                footprint.SetPosition(vec)
                footprint.SetOrientationDegrees(np.rad2deg(angle_led))
                led_num += 1

        pcb.Save('test.kicad_pcb')


    def load_config(self, config):
        return config if isinstance(config, Config) else Config(filename=config)

    def print_config(self):
        print_nested(self.config, 1)

    def to_mm(self, v):
        return v if self.config['units']['length'] == 'mm' else inch_to_mm(v) 

    def to_rad(self, v):
        return v if self.config['units']['angle'] == 'rad' else np.deg2rad(v)


# ----------------------------------------------------------------------------------

def print_nested(d, indent_num=0, indent_step=2):
    indent_str = ' '*indent_step*indent_num
    if not isinstance(d,dict):
        print(f'{indent_str}d')
    else:
        for k, v in d.items():
            if isinstance(v,dict):
                print(f'{indent_str}{k}:')
                print_nested(v,indent_num+1, indent_step)
            else:
                print(f'{indent_str}{k}: {v}')
            

