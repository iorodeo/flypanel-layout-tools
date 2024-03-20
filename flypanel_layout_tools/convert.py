import scipy.constants as constants
import pcbnew

def inch_to_mm(val):
    return 1e3*constants.inch*val

def mm_to_inch(val):
    return 1e-3*val/constants.inch

def pos_to_pcbnew_vec(p):
    x, y = p
    xi = pcbnew.FromMM(x)
    yi = pcbnew.FromMM(y)
    return pcbnew.VECTOR2I(xi,yi)
