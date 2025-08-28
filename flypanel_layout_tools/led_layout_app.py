import pathlib
import click
from .config import Config 
from .led_array import LedArray
from .led_array import DiagonalMultiColorLedArray
from .led_array import BoustrophedonMultiColorLedArray

@click.command()
@click.help_option('-h', '--help')
@click.option('-c', '--conf', default='config.toml', help='configuration file')
@click.option('-f', '--file', help='kicad pcb file')

def cli(conf, file):
    """
    Panel pcb led array layout tool. Place led components on the .kicad_pcb file
    into rectangular array based on the config file parameters. 

    """
    print()
    print(f'panel-led-layout')
    print(f'----------------')
    print(f'config:    {conf}')
    print()

    config = Config(filename=conf)
    match config['pcb']['led']['pattern']:
        case 'boustrophedon':
            layout = BoustrophedonMultiColorLedArray(config)
        case 'diagonal':
            layout = DiagonalMultiColorLedArray(config)
        case _:
            layout = LedArray(config)
    if file is not None:
        layout.place_components(file)

