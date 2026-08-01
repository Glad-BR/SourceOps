import os
import sys
import json
import time
import subprocess
import numpy as np
from pathlib import Path

from ...utils.logger import log

from multiprocessing import shared_memory

# Cache the sourcepp package root globally.
import sourcepp
_SOURCEPP_ROOT = str(Path(sourcepp.__file__).resolve().parent.parent)



# Run Once on startup
worker_file = Path(__file__).parent / 'vtfpp_worker.py'

log.debug(worker_file.resolve())

with open(worker_file.resolve(), 'r', encoding="utf-8") as file:
    worker_code = file.read()


#All this just because sourcepp doesn’t release the GIL
def create_vtf(
        image: np.ndarray,
        output_path: str | Path,
        options = None,
        flags = None,
        exists_ok: bool = True
    ):

    start = time.perf_counter()
    output_path = Path(output_path).resolve()

    if image is None or not output_path:
        return None

    if exists_ok and output_path.exists():
        log.info(f"VTF {output_path.name} already exists. Skipping.")
        return output_path

    output_path.parent.mkdir(exist_ok=True, parents=True)

    from sourcepp import vtfpp

    # Options mapping setup
    options_dict = {
        "output_format": vtfpp.ImageFormat.DXT5.value,
        "version": getattr(options, "version", 2),
        "flags": 0,
        "compute_mips": getattr(options, "compute_mips", True),
        "compute_thumbnail": getattr(options, "compute_thumbnail", True),
        "compute_reflectivity": getattr(options, "compute_reflectivity", True)
    }

    if flags:
        output_mask = 0
        for flag in flags:
            output_mask |= flag.value
        options_dict["flags"] = output_mask

    if options:
        options_dict["output_format"] = options.output_format.value

    image = np.clip(image * 255.0, 0, 255).astype(np.uint8)

    if image.ndim == 2:
        HEIGHT, WIDTH = image.shape
        FORMAT = vtfpp.ImageFormat.I8.value
    elif image.ndim == 3:
        HEIGHT, WIDTH, CHANNELS = image.shape
        format_map = {
            1: vtfpp.ImageFormat.I8.value,
            2: vtfpp.ImageFormat.IA88.value,
            3: vtfpp.ImageFormat.RGB888.value,
            4: vtfpp.ImageFormat.RGBA8888.value
        }
        if CHANNELS not in format_map:
            raise ValueError(f"Unsupported number of channels: {CHANNELS}")
        FORMAT = format_map[CHANNELS]
    else:
        raise ValueError(f"Unsupported number of dimensions: {image.ndim}")

    image_shm = shared_memory.SharedMemory(create=True, size=image.nbytes)
    image_shm.buf[:image.nbytes] = image.tobytes()

    config_payload = {
        "shared_memory_name": image_shm.name,
        "image_size": image.nbytes,
        "np_format": FORMAT,
        "width": WIDTH,
        "height": HEIGHT,
        "options": options_dict,
        "vtf_path": str(output_path)
    }

    # Replicate environment paths.
    env = os.environ.copy()
    existing_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{_SOURCEPP_ROOT}{os.pathsep}{existing_path}" if existing_path else _SOURCEPP_ROOT

    try:
        result = subprocess.run(
            [sys.executable, "-c", worker_code],
            capture_output=True,
            text=True,
            input=json.dumps(config_payload),
            env=env
        )
    finally:
        image_shm.close()
        try:
            image_shm.unlink()
        except FileNotFoundError:
            pass

    if result.returncode != 0:
        log.critical(f"Subprocess worker crashed! StdErr:\n{result.stderr}")
        raise RuntimeError(f"VTF generation subprocess failed for {output_path.name}")

    err = None
    for line in result.stdout.splitlines():
        if line.startswith("WORKER_RESULT:"):
            err = line.split(":", 1)
            break

    if not output_path.exists():
        log.critical('VTF creation finished but output was not found')
        log.critical(output_path)
        return FileNotFoundError

    log.info(f"VTF Creation for {output_path.name} finished in {time.perf_counter() - start:.2f}s")
    return err
