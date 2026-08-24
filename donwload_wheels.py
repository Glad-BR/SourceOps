from pathlib import Path

from concurrent.futures import ThreadPoolExecutor

import subprocess
import sys

import click


from rich import print
from rich.prompt import Confirm

wheels = Path('./wheels')

VERSIONS = [
#    '311',
    '313',
]

def main():
    with ThreadPoolExecutor() as executor:
        futures = []
        for ver in VERSIONS:

            args1 = [sys.executable, '-m', 'pip', 'download', '--only-binary=:all:', f'--python-version={ver}', '--platform=win_amd64', '-d', str(wheels), '-r', 'requirements.txt']
            args2 = [sys.executable, '-m', 'pip', 'download', '--only-binary=:all:', f'--python-version={ver}', '-d', str(wheels), '-r', 'requirements.txt']

            futures.append( executor.submit(subprocess.check_call, args1) )
            futures.append( executor.submit(subprocess.check_call, args2) )
    

    wls = list(wheels.glob('*.whl'))

    for i in sorted(wls):
        print(f'  "./{str(i)}",')


    if click.confirm('Build extension?', default=True):
        print('Do something')
        args = ['blender', '--command', 'extension', 'build']

        if click.confirm('--split-platforms', default=False):
            args.append('--split-platforms')

        subprocess.check_call(args)

    #subprocess.check_call(args=['blender', '--command', 'extension', 'install-file', '-r', 'user_default', '-e'])




if __name__ == '__main__':
    main()



    



