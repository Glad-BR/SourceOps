import os
import cv2
import sys
import json
import time
import subprocess
import numpy as np
from pathlib import Path
from ...utils import common 
from ...utils.logger import log
from multiprocessing.managers import SharedMemoryManager

from collections.abc import Iterable

# Cache the sourcepp package root globally.
import sourcepp
from sourcepp import vtfpp
_SOURCEPP_ROOT = str(Path(sourcepp.__file__).resolve().parent.parent)

# Run Once on startup
worker_file = Path(__file__).parent / 'vtfpp_worker.py'

log.debug(worker_file.resolve())

with open(worker_file.resolve(), 'r', encoding="utf-8") as file:
    worker_code = file.read()


def create_vtf(
        image: np.ndarray,
        output_path: str | os.PathLike,
        options: vtfpp.VTF.CreationOptions = None,
        flags: Iterable[vtfpp.VTF.Flags] = None,
        exists_ok: bool = False,
        use_workers: bool = True
    ):

    start = time.perf_counter()
    output_path = Path(output_path).resolve()

    if image is None or not output_path:
        return None

    if exists_ok and output_path.exists():
        log.info(f"VTF {output_path.name} already exists. Skipping.")
        return output_path

    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    if flags:
        output_mask = 0
        for flag in flags:
            output_mask |= flag.value
        options.flags = output_mask

    if image.ndim == 2:
        HEIGHT, WIDTH = image.shape
        FORMAT = vtfpp.ImageFormat.R32F.value
    elif image.ndim == 3:
        HEIGHT, WIDTH, CHANNELS = image.shape
        format_map = {
            1: vtfpp.ImageFormat.R32F.value,
            2: vtfpp.ImageFormat.RG3232F.value,
            3: vtfpp.ImageFormat.RGB323232F.value,
            4: vtfpp.ImageFormat.RGBA32323232F.value
        }
        if CHANNELS not in format_map:
            raise ValueError(f"Unsupported number of channels: {CHANNELS}")
        FORMAT = format_map[CHANNELS]
    else:
        raise ValueError(f"Unsupported number of dimensions: {image.ndim}")

    image = np.ascontiguousarray(np.clip(image, 0.0, 1.0), dtype=np.float32)

    try:
        import bpy
        use_workers = common.get_prefs(bpy.context).vtf_use_workers
    except Exception as e:
        log.exception(e)


    #All this just because sourcepp doesn’t release the GIL
    if use_workers:
        with SharedMemoryManager() as smm:
            image_shm = smm.SharedMemory(size=image.nbytes)
            image_shm.buf[:image.nbytes] = image.tobytes()
            log.debug(f"Created shared memory: {image_shm}")

            # Deconstruct
            options_payload = common.serialize_obj(options)
            options_payload["resize_bounds"] = common.serialize_obj(options.resize_bounds)

            config_payload = {
                "shared_memory_name": image_shm.name,
                "image_size": image.nbytes,
                "np_format": FORMAT,
                "width": WIDTH,
                "height": HEIGHT,
                "options": options_payload,
                "vtf_path": str(output_path)
            }
            del image

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
            except Exception as e:
                log.exception(f"Failed to start subprocess for VTF creation: {e}")


        if result.returncode != 0:
            log.critical(f"Subprocess worker crashed! StdErr:")
            log.critical(result.stderr)
            raise RuntimeError(f"VTF generation subprocess failed for {output_path.name}")

        err = None
        for line in result.stdout.splitlines():
            if line.startswith("WORKER_RESULT:"):
                err = line.split(":", 1)
                break

    else:
        err = vtfpp.VTF.create_and_bake(
            image_data=image.tobytes(),
            format=FORMAT,
            width=WIDTH,
            height=HEIGHT,
            creation_options=options,
            vtf_path=str(output_path),
        )
        del image

    if not output_path.exists():
        log.critical('VTF creation finished but output was not found')
        log.critical(output_path)
        return FileNotFoundError

    log.info(f"VTF Creation for {output_path.name} finished in {time.perf_counter() - start:.2f}s")
    return err
