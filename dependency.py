import sys
import importlib
import subprocess

from pathlib import Path

REQUIRED_MODULES = {
#    'PIL' : 'Pillow',
#    'rich' : 'rich',
    'numpy' : 'numpy',
    'sourcepp': 'sourcepp',
    'cv2' : 'opencv-python-headless',
    'logging': 'logging',
}


target = Path(__file__).resolve().parent / 'deps'
print(f"Deps Target Path: {target}")


def install(package, target:Path):
    target.mkdir(exist_ok=True)
    subprocess.check_call( [ sys.executable, '-m', 'pip', 'install', package, '--target', str(target.resolve()) ] )

def run():
    for module, pkg in REQUIRED_MODULES.items():
        try:
            importlib.import_module(module)
            print(f'Module {module} found')
        except Exception as e:
            print(f'Installing {pkg}')
            install(pkg, target)



def register():
    target.mkdir(exist_ok=True)

    dir_str = str(target)
    if dir_str not in sys.path:
        sys.path.insert(0, dir_str)

    run()


def unregister():

    dir_str = str(target)
    if dir_str not in sys.path:
        sys.path.remove(dir_str)













