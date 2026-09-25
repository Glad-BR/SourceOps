import sys
import json
from sourcepp import vtfpp
from multiprocessing import shared_memory


def main():
    cfg = json.load(sys.stdin)

    image_shm = shared_memory.SharedMemory(name=cfg["shared_memory_name"], track=False)
    try:
        image_data = bytes(image_shm.buf[:cfg["image_size"]])
        options_payload = cfg["options"]
        # Reconstruct
        creation_options = vtfpp.VTF.CreationOptions()

        for name, val in options_payload["resize_bounds"].items():
            setattr(creation_options.resize_bounds, name, val)

        for name, val in options_payload.items():
            if name != "resize_bounds":
                setattr(creation_options, name, val)


        err = vtfpp.VTF.create_and_bake(
            image_data=image_data,
            format=vtfpp.ImageFormat(cfg["np_format"]),
            width=cfg["width"],
            height=cfg["height"],
            creation_options=creation_options,
            vtf_path=cfg["vtf_path"],
        )
        del image_data
        print(f"WORKER_RESULT:{err}")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
