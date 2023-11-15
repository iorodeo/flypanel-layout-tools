import scipy.constants as constants

def inch_to_mm(val):
    return 1e3*constants.inch*val

def mm_to_inch(val):
    return 1e-3*val/constants.inch
