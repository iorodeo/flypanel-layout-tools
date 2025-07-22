import pathlib
import click
from .led_array import MultiColorLedArray

@click.command()
@click.help_option('-h', '--help')
@click.option('-c', '--conf', default='config.toml', help='configuration file')
@click.option('-f', '--file', help='kicad pcb file')

def cli(conf, file):
    """
    Tool layout led array in .kicad_pcb file for the panel pcbs.  placing the components on
    a .kicad_pcb file. 

    """
    print()
    print(f'panel-led-layout')
    print(f'----------------')
    print(f'config:    {conf}')
    print()
    layout = MultiColorLedArray(conf)
    if file is not None:
        layout.place_components(file)

