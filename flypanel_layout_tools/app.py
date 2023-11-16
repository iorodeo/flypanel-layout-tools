import click
from .ring_layout import RingLayout

@click.command()
@click.help_option('-h', '--help')
@click.option('-c', '--config', help='configuration file')
@click.option('-p', '--pcb', help='kicad pcb file')
@click.argument('geometry')
def cli(geometry, config, pcb):
    """
    Tool for generating flypanel arena layouts and placing the components on
    a .kicad_pcb file. 

    GEOMETRY = arena geometry, e.g. ring
    """
    if geometry.lower() == 'ring':
        print('running ring layout')
    else:
        print()
        print(f"flypanel arena geometry = '{geometry}' not supported yet.")
        print()

