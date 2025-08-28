import pathlib
import pcbnew
import collections
import numpy as np
from .config import Config 
from .convert import inch_to_mm
from .convert import pos_to_pcbnew_vec 


class LedArray:

    """ Normal single color led array layout for panels pcbs """

    def __init__(self, config):
        self.config = self.load_config(config)
        self.print_config()
        print()

    def place_components(self, filename):
        nrows = self.config['pcb']['led']['nrows']
        ncols = self.config['pcb']['led']['ncols']
        dim = self.config['pcb']['led']['ncols']
        angle_led = self.to_rad(self.config['pcb']['led']['angle'])
        pcb = pcbnew.LoadBoard(filename)
        for i in range(ncols):
            for j in range(nrows):
                sch_ind = i,j
                pos_ind = self.sch_to_pos_ind(*sch_ind)
                ref = self.label_from_sch_ind(*sch_ind)
                pos = self.posxy_from_pos_ind(*pos_ind)
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

    def label_from_sch_ind(self,i,j):
        """ 
        Return the led label from the led's index values when laid out columnwise
        in the schematic 
        """
        dim = self.config['pcb']['led']['dim']
        ref_prefix = self.config['pcb']['led']['ref_prefix']
        k = 1 + i + j*dim

        return f'{ref_prefix}{k}'

    def sch_to_pos_ind(self, i, j):
        return i, j

    def posxy_from_pos_ind(self, i, j):
        w_pcb = self.to_mm(self.config['pcb']['size_x'])
        h_pcb = self.to_mm(self.config['pcb']['size_y'])
        cx_pcb = self.to_mm(self.config['pcb']['center_x'])
        cy_pcb = self.to_mm(self.config['pcb']['center_y'])
        try: 
            dim = self.config['pcb']['led']['dim']
        except KeyError:
            nrows = self.config['pcb']['led']['nrows']
            ncols = self.config['pcb']['led']['ncols']
        else:
            nrows = dim 
            ncols = dim
        dx_led = w_pcb/ncols   
        dy_led = h_pcb/nrows   
        w_led = (ncols-1)*dx_led   
        h_led = (nrows-1)*dy_led   
        x_led = cx_pcb + j*dx_led - 0.5*w_led  
        y_led = cy_pcb + i*dy_led - 0.5*h_led
        pos = (x_led, y_led)
        return pos



# ----------------------------------------------------------------------------------

class DiagonalMultiColorLedArray(LedArray):

    """ Diagonal multicolor led layout for panels pcbs.  """

    def __init__(self, config):
        super().__init__(config)

    def place_components(self, filename):
        print('input file:  ', filename)
        dim = self.config['pcb']['led']['dim']
        angle_led = self.to_rad(self.config['pcb']['led']['angle'])
        pcb = pcbnew.LoadBoard(filename)

        for i in range(0,dim): # cols
            for j in range(0,dim): # rows
                sch_ind = i, j
                pos_ind = self.sch_to_pos_ind(*sch_ind)
                ref = self.label_from_sch_ind(*sch_ind)
                pos = self.posxy_from_pos_ind(*pos_ind)
                footprint = pcb.FindFootprintByReference(ref)
                vec = pos_to_pcbnew_vec(pos)
                footprint.SetPosition(vec)
                footprint.SetOrientationDegrees(np.rad2deg(angle_led))

        inp_path = pathlib.Path(filename)
        out_path = pathlib.Path(inp_path.parent, f'{inp_path.stem}_mod{inp_path.suffix}')
        print('output file: ', out_path)
        pcb.Save(str(out_path))

    def sch_to_pos_ind(self, i, j):
        dim = self.config['pcb']['led']['dim']
        return i, (i+j)%dim

    


class BoustrophedonMultiColorLedArray(LedArray):

    """ 
    Boustrophedon 'like the ox turns' or 'as the ox plows' multicolor led
    layout for panels pcbs.
    """

    def __init__(self, config):
        super().__init__(config)

    def place_components(self, filename):
        print('input file:  ', filename)
        dim = self.config['pcb']['led']['dim']
        angle_led = self.to_rad(self.config['pcb']['led']['angle'])
        pcb = pcbnew.LoadBoard(filename)

        for i in range(dim): # cols
            for j in range(dim): # rows
                sch_ind = i, j
                pos_ind = self.sch_to_pos_ind(*sch_ind)
                ref = self.label_from_sch_ind(*sch_ind)
                pos = self.posxy_from_pos_ind(*pos_ind)
                footprint = pcb.FindFootprintByReference(ref)
                vec = pos_to_pcbnew_vec(pos)
                footprint.SetPosition(vec)
                footprint.SetOrientationDegrees(np.rad2deg(angle_led))

        inp_path = pathlib.Path(filename)
        out_path = pathlib.Path(inp_path.parent, f'{inp_path.stem}_mod{inp_path.suffix}')
        print('output file: ', out_path)
        pcb.Save(str(out_path))

    def sch_to_pos_ind(self,i,j):
        dim = self.config['pcb']['led']['dim']
        step = self.config['pcb']['led']['step']
        if step%2 != 0:
            raise ValueError('step must be divisible by 2')
        if dim%2 != 0:
            raise ValueError('dim must be divisible by 2')
        if j%step < step//2:
            if i<dim//2:
                pos_ind = 2*i, j
            else:
                pos_ind = 2*(20 - (i+1)), step//2 + j 
        else:
            if i<dim//2:
                pos_ind = 2*i + 1, j - step//2 
            else:
                pos_ind = 2*(20 - (i+1)) + 1, j 
        return pos_ind






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
            

