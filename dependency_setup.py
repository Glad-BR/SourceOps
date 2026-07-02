import importlib
import subprocess
import sys
from pathlib import Path


REQUIRED_MODULES = ('numpy', 'PIL', 'sourcepp')


def _get_virtualenv_python(base_dir: Path) -> Path:
    venv_dir = base_dir / '.venv'
    if sys.platform.startswith('win'):
        return venv_dir / 'Scripts' / 'python.exe'
    return venv_dir / 'bin' / 'python'


def _ensure_virtualenv(base_dir: Path) -> Path:
    venv_python = _get_virtualenv_python(base_dir)
    if not venv_python.exists():
        subprocess.check_call([sys.executable, '-m', 'venv', str(base_dir / '.venv')])
    return venv_python


def _add_virtualenv_to_path(base_dir: Path) -> Path:
    print('Creating / activating virtual environment...')
    venv_python = _ensure_virtualenv(base_dir)
    site_packages = subprocess.check_output(
        [str(venv_python), '-c', 'import sysconfig; print(sysconfig.get_paths()["purelib"])'],
        text=True,
    ).strip()

    if site_packages and site_packages not in sys.path:
        sys.path.insert(0, site_packages)

    print(f"SourceOps virtual environment: {venv_python}")
    return venv_python


def _dependencies_available() -> bool:
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            return False
    return True


def check_dependencies(base_dir: Path | None = None) -> bool:
    repo_dir = Path(__file__).resolve().parent if base_dir is None else Path(base_dir).resolve()

    _add_virtualenv_to_path(repo_dir)
    if _dependencies_available():
        return True

    venv_python = _ensure_virtualenv(repo_dir)
    req_file = repo_dir / 'requirements.txt'

    try:
        subprocess.check_call([str(venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([str(venv_python), '-m', 'pip', 'install', '-r', str(req_file)])
    except subprocess.CalledProcessError as exc:
        raise RuntimeError('Failed to install addon dependencies into the local virtual environment.') from exc

    _add_virtualenv_to_path(repo_dir)
    if not _dependencies_available():
        raise RuntimeError('Addon dependencies are still unavailable after installation.')

    return True
