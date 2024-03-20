import sys
from flypanel_layout_tools import LedArray

config_file = sys.argv[1]
kicad_file = sys.argv[2]

print()
print(f'config file: {config_file}')
print(f'kicad file:  {kicad_file}')
print()

layout = LedArray(config_file)
layout.print_config()
print()


layout.place_components(kicad_file)




