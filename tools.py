from struct import calcsize
from struct import pack
from struct import unpack
import tempfile
import os


def add_resolution_to_jpg(filename, resolution):
    """add_resolution_to_jpg: Agrega info de la resolución al archivo

    Debido a problemas a la hora de incrustar imagenes en el Word resulta
    necesario agregar al header del JPG la información de la resolución
    Vertical y horizontal, debido a que opencv no salva esta información.

    Args:
        filename (str): Path completo al archivo jpg
        resolution (int): Resolución

    Example:
        >>> add_resolution_to_jpg("c:\\prueba.jpg", 150) # 150 dpi

    """
    struct_fmt = '>6s5sHBHH'
    struct_len = calcsize(struct_fmt)

    with open(filename, "rb") as f:
        header = unpack(struct_fmt, f.read(struct_len))
        data = f.read()

    with open(filename, "wb") as f:
        f.write(pack(
                    struct_fmt,
                    header[0],
                    header[1],
                    header[2],
                    header[3],
                    resolution,
                    resolution)
                )
        f.write(data)


def expand_filename(filename):
    """expand_filename: Expansión de un path con keywords

    Args:
        filename (str): Path completo a un archivo con keywords

    Example:
        >>> expand_filename("{Desktop}")
    """

    replace_paths = {
        '{desktop}': os.path.join(os.path.expanduser('~'), 'Desktop'),
        '{tmpdir}': tempfile.gettempdir(),
        '{tmpfile}': tempfile.mktemp()
    }

    for path_keyword in replace_paths:
        if path_keyword in filename:
            filename.replace(path_keyword, replace_paths[path_keyword]())

    return filename
