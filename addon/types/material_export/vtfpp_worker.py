import json
import sys
from pathlib import Path
from sourcepp import vtfpp

from multiprocessing import resource_tracker, shared_memory

if __name__ == "__main__":
    cfg = json.load(sys.stdin)

    image_shm = shared_memory.SharedMemory(name=cfg["shared_memory_name"])
    # This process only borrows the segment; the parent owns its lifetime.
    # Prevent this interpreter's resource tracker from unlinking it on exit.
    resource_tracker.unregister(image_shm._name, "shared_memory")
    try:
        # vtfpp consumes the buffer synchronously.  Copy it before closing the
        # shared-memory handle so the native binding receives ordinary bytes.
        image_data = bytes(image_shm.buf[:cfg["image_size"]])

        opts = cfg["options"]
        native_options = vtfpp.VTF.CreationOptions()
        native_options.output_format = vtfpp.ImageFormat(opts["output_format"])
        native_options.version = opts["version"]
        native_options.flags = opts["flags"]
        native_options.compute_mips = opts["compute_mips"]
        native_options.compute_thumbnail = opts["compute_thumbnail"]
        native_options.compute_reflectivity = opts["compute_reflectivity"]

        native_format = vtfpp.ImageFormat(cfg["np_format"])

        err = vtfpp.VTF.create_and_bake(
            image_data=image_data,
            format=native_format,
            width=cfg["width"],
            height=cfg["height"],
            creation_options=native_options,
            vtf_path=Path(cfg["vtf_path"])
        )
        print(f"WORKER_RESULT:{err}")
    finally:
        image_shm.close()
