from struct import calcsize
from struct import pack
from struct import unpack
import logging
import tempfile
import os
import sys
import re
import subprocess
import warnings
import numpy as np
import cv2


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


def loginfo(msg, printmsg=False):
    if printmsg:
        print(msg)
    logging.info(msg.replace("|", " "))


def logerror(msg):
    logging.error(msg.replace("|", " "))


def resource_path(relative):
    """Obtiene un path, toma en consideración el uso de pyinstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)


def pdf_count_pages(filename, pdfinfo_bin, rxcountpages):
    """pdf_get_metadata: cuenta la cantidad de páginas de un PDF

    Args:
        filename(str): Path completo al archivo PDF
    """
    loginfo("Get PDF info")
    cmdline = '{0} {1}'.format(pdfinfo_bin, filename)
    loginfo(cmdline)
    process = subprocess.Popen(cmdline.split(" "), stdout=subprocess.PIPE)
    out, err = process.communicate()
    rxcountpages = re.compile(rxcountpages, re.MULTILINE | re.DOTALL)
    m = re.findall(rxcountpages, out.decode('latin1'))

    return int(m[0]) if m else None


def make_wide(formatter, w=120, h=36):
    """Return a wider HelpFormatter, if possible."""
    try:
        # https://stackoverflow.com/a/5464440
        # beware: "Only the name of this class is considered a public API."
        kwargs = {'width': w, 'max_help_position': h}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        warnings.warn("argparse help formatter failed, falling back.")
        return formatter


def clean_blank_area(img):

    # img = img[:-20, :-20]  # Perform pre-cropping
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = 255*(gray < 128).astype(np.uint8)  # To invert the text to white
    gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, np.ones((2, 2), dtype=np.uint8))  # Perform noise filtering
    coords = cv2.findNonZero(gray)  # Find all non-zero points (text)
    x, y, w, h = cv2.boundingRect(coords)  # Find minimum spanning bounding box

    margin = 0
    x = x - margin
    y = y - margin
    w = w + margin*2
    h = h + margin*2
    rect = img[y:y+h, x:x+w]  # Crop the image - note we do this on the original image
    return rect
