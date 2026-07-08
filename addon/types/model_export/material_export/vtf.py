import time
import numpy as np
from pathlib import Path
from sourcepp import vtfpp


def create_vtf(
        image: np.ndarray,
        output_path: str|Path,
        options = None,
        flags= None,
        exists_ok: bool = True
    ):

    start = time.perf_counter()
    print('Starting VTF Creation')

    if image is None: return None
    if not output_path: return None

    if exists_ok and output_path.exists():
        print(f'VTF {output_path} Already Exists, exists_ok={exists_ok}. Skipping')
        return output_path

    if not options:
        options = vtfpp.VTF.CreationOptions()
        options.output_format = vtfpp.ImageFormat.DXT5
        options.version = 2

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(exist_ok=True, parents=True)

    # Just to make sure
    options.compute_mips         = True if not options.compute_mips         else options.compute_mips
    options.compute_thumbnail    = True if not options.compute_thumbnail    else options.compute_thumbnail
    options.compute_reflectivity = True if not options.compute_reflectivity else options.compute_reflectivity

    image = np.clip(image * 255.0, 0, 255).astype(np.uint8)

    if image.ndim == 2:
        HEIGHT, WIDTH = image.shape
        DATA = image.tobytes()
        FORMAT = vtfpp.ImageFormat.I8
    elif image.ndim == 3:
        HEIGHT, WIDTH, CHANNELS = image.shape
        if CHANNELS == 1:
            DATA = image.tobytes()
            FORMAT = vtfpp.ImageFormat.I8
        elif CHANNELS == 2:
            DATA = image.tobytes()
            FORMAT = vtfpp.ImageFormat.IA88
        elif CHANNELS == 3:
            DATA = image.tobytes()
            FORMAT = vtfpp.ImageFormat.RGB888
        elif CHANNELS == 4:
            DATA = image.tobytes()
            FORMAT = vtfpp.ImageFormat.RGBA8888
        else:
            raise ValueError(f"Unsupported number of channels: {CHANNELS}")
    else:
        raise ValueError(f"Unsupported number of dimensions: {image.ndim}")


    vtf = vtfpp.VTF.create(
        image_data=DATA,
        format=FORMAT,
        width=WIDTH,
        height=HEIGHT,
        creation_options=options
    )

    if flags:
        for flag in flags:
            vtf.add_flags(flag.value)

    err = vtf.bake_to_file(vtf_path=output_path)

    if output_path.exists():
        print('VTF Created', output_path, err, f'took {time.perf_counter()-start:.3f}s')
        return output_path
    else:
        print(err)