import pathlib
import click
from .ring_layout import RingLayout

@click.command()
@click.help_option('-h', '--help')
@click.option('-c', '--conf', default='config.toml', help='configuration file')
@click.option('-f', '--file', help='kicad pcb file')
@click.option('--plot/--no-plot', ' /-n', default=True)

@click.argument('geom')
def cli(geom, conf, file, plot):
    """
    Tool for generating flypanel arena layouts and placing the components on
    a .kicad_pcb file. 

    GEOM = arena geometry, e.g. ring
    """
    print()
    print(f'flypanel-layout')
    print(f'---------------')
    if geom.lower() == 'ring':
        print(f'geometry:  {geom}')
        print(f'config:    {conf}')
        print(f'plot:      {plot}')
        print()
        layout = RingLayout(conf,plot)
        if file is not None:
            layout.place_components(file)
    else:
        print()
        print(f"arena geometry = '{geometry}' not supported yet.")
        print()

