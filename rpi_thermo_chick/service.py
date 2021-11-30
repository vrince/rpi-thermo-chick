import click
from appdirs import user_config_dir
from os import path, makedirs
from shutil import copyfile
import json

config_dir = user_config_dir('rpi-thermo-chick')
install_dir = '/lib/systemd/system'
module_dir = path.dirname(__file__)

default_config = {
    'relays': [{ 'pin': 4},{ 'pin': 7}],
    'thermometers': [{ 'device': '28-3c01d0751fcd'}, { 'device': '28-3c01d075db96'}]}

@click.command()
@click.argument('action')
def cli(action):
    """
    rpi-thermo-chick: 🐔🔥 servive

    ACTIONS : 
    * configure (create configuration file)
    * install (install service file)
    """
    if action == 'configure':
        config_file = path.join(config_dir, 'config.json')
        print(f'🔧 creating {config_file} ...')
        if not path.exists(config_file):
            makedirs(config_dir, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(default_config, f)

    elif action == 'install':
        service_filename = 'rpi-thermo-chick.service'
        service_file = path.join(module_dir, service_filename)
        installed_service_file = path.join(install_dir, service_filename)
        print(f'🔧 installing {installed_service_file} ...')
        if not path.exists(installed_service_file):
            copyfile(service_file, installed_service_file)
    else:
        print('unknown action')

if __name__ == "__main__":
    cli()