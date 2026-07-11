import os
import sys
import json
import time
import uuid
import tempfile
import subprocess
import numpy as np
from pathlib import Path

# Cache path lookups and system temporary folder globally
import sourcepp
_SOURCEPP_ROOT = str(Path(sourcepp.__file__).resolve().parent.parent)
_SHARED_TMP_DIR = Path(tempfile.gettempdir()).resolve()

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
        print(f"VTF {output_path.name} already exists. Skipping.")
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

    task_id = uuid.uuid4().hex
    data_file = _SHARED_TMP_DIR / f"vtf_img_{task_id}.raw"
    config_file = _SHARED_TMP_DIR / f"vtf_cfg_{task_id}.json"
    worker_script = _SHARED_TMP_DIR / f"vtf_run_{task_id}.py"

    data_file.write_bytes(image.tobytes())
    
    config_payload = {
        "raw_path": str(data_file),
        "format_value": FORMAT,
        "width": WIDTH,
        "height": HEIGHT,
        "options": options_dict,
        "vtf_path": str(output_path)
    }
    config_file.write_text(json.dumps(config_payload), encoding="utf-8")

    worker_code = f"""
import json
from pathlib import Path
from sourcepp import vtfpp

if __name__ == "__main__":
    with open("{config_file}", "r") as f:
        cfg = json.load(f)
        
    image_data = Path(cfg["raw_path"]).read_bytes()
    
    opts = cfg["options"]
    native_options = vtfpp.VTF.CreationOptions()
    native_options.output_format = vtfpp.ImageFormat(opts["output_format"])
    native_options.version = opts["version"]
    native_options.flags = opts["flags"]
    native_options.compute_mips = opts["compute_mips"]
    native_options.compute_thumbnail = opts["compute_thumbnail"]
    native_options.compute_reflectivity = opts["compute_reflectivity"]

    native_format = vtfpp.ImageFormat(cfg["format_value"])

    err = vtfpp.VTF.create_and_bake(
        image_data=image_data,
        format=native_format,
        width=cfg["width"],
        height=cfg["height"],
        creation_options=native_options,
        vtf_path=Path(cfg["vtf_path"])
    )
    print(f"WORKER_RESULT:{{err}}")
"""
    worker_script.write_text(worker_code.strip(), encoding="utf-8")

    # Replicate environment paths 
    env = os.environ.copy()
    existing_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{_SOURCEPP_ROOT}{os.pathsep}{existing_path}" if existing_path else _SOURCEPP_ROOT

    result = subprocess.run(
        [sys.executable, str(worker_script)],
        cwd=str(_SHARED_TMP_DIR),
        capture_output=True,
        text=True,
        env=env
    )

    try:
        data_file.unlink(missing_ok=True)
        config_file.unlink(missing_ok=True)
        worker_script.unlink(missing_ok=True)
    except OSError:
        pass

    if result.returncode != 0:
        print(f"Subprocess worker crashed! StdErr:\n{result.stderr}")
        raise RuntimeError(f"VTF generation subprocess failed for {output_path.name}")

    err = None
    for line in result.stdout.splitlines():
        if line.startswith("WORKER_RESULT:"):
            err = line.split(":", 1)
            break

    print(f"VTF Creation for {output_path.name} finished in {time.perf_counter() - start:.2f}s")
    return err
