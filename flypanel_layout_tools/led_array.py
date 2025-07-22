import pcbnew
import collections
import numpy as np
from .config import Config 
from .convert import inch_to_mm
from .convert import pos_to_pcbnew_vec 




class LedArray:

    def __init__(self, config):
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

class MultiColorLedArray(LedArray):

    def __init__(self, config):
        super().__init__(config)
        self.print_config()
        print()

    def place_components(self, filename):
        w_pcb = self.to_mm(self.config['pcb']['size_x'])
        h_pcb = self.to_mm(self.config['pcb']['size_y'])
        cx_pcb = self.to_mm(self.config['pcb']['center_x'])
        cy_pcb = self.to_mm(self.config['pcb']['center_y'])

        dim = self.config['pcb']['led']['dim']
        angle_led = self.to_rad(self.config['pcb']['led']['angle'])
        num_color = self.config['pcb']['led']['ncolor']

        nleds = dim**2
        dx_led = w_pcb/dim        # LED x spacing
        dy_led = h_pcb/dim        # LED y spacing
        w_led = (dim-1)*dx_led  # width  of LED array
        h_led = (dim-1)*dy_led  # height of LED array

        pcb = pcbnew.LoadBoard(filename)

        for i in range(0,dim): # cols
            for j in range(0,dim): # rows

                #ref = self.label_from_schem_ind(i,j)
                ref = self.label_from_pos_ind(i,j)
                y_led = cx_pcb + i*dx_led - 0.5*w_led  
                x_led = cy_pcb + j*dy_led - 0.5*h_led
                pos = (x_led, y_led)

                footprint = pcb.FindFootprintByReference(ref)
                vec = pos_to_pcbnew_vec(pos)
                footprint.SetPosition(vec)
                footprint.SetOrientationDegrees(np.rad2deg(angle_led))

        pcb.Save('test.kicad_pcb')

    def label_from_schem_ind(self,i,j):
        """ 
        Return the led label from the led's index values when laid out columnwise
        in the schematic 
        """
        dim = self.config['pcb']['led']['dim']
        ref_prefix = self.config['pcb']['led']['ref_prefix']
        k = 1 + i + j*dim
        return f'{ref_prefix}{k}'
    
    def label_from_pos_ind(self,i,j):
        """ 
        Return the led label from the led's position in panel array 
        """
        i_pcb, j_pcb = self.pcb_ind_from_schem_ind(i,j)
        return self.label_from_schem_ind(i_pcb,j_pcb)
    
    def pcb_ind_from_schem_ind(self, i,j):
        """ 
        Return the led's position in the panel array given its  index
        values in the schematic
        """
        dim = self.config['pcb']['led']['dim']
        return i, (j-i)%dim


# Utility functions
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
            

