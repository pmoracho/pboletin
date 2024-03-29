#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Patricio Moracho <pmoracho@gmail.com>
#
# pboletin.py
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License
# as published by the Free Software Foundation. A copy of this license should
# be included in the file GPL-3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""
pboletin
========

Procesamiento de los boletines de marcas y patentes de Argentina

"""

__author__ = "Patricio Moracho <pmoracho@gmail.com>"
__appname__ = "pboletin"
__appdesc__ = "Procesamiento de boletines"
__license__ = 'GPL v3'
__copyright__ = "(c) 2018, %s" % (__author__)
__version__ = "1.0"
__date__ = "2018/06/02"

import argparse
import gettext
import logging
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

try:
    from gettext import gettext as _
    gettext.textdomain('padrondl')

    def my_gettext(s):
        """my_gettext: Traducir algunas cadenas de argparse."""
        current_dict = {
            'usage: ': 'uso: ',
            'optional arguments': 'argumentos opcionales',
            'show this help message and exit': 'mostrar esta ayuda y salir',
            'positional arguments': 'argumentos posicionales',
            'the following arguments are required: %s': 'los siguientes argumentos son requeridos: %s',
            'show program''s version number and exit': 'Mostrar la versión del programa y salir',
            'expected one argument': 'se espera un valor para el parámetro',
            'expected at least one argument': 'se espera al menos un valor para el parámetro'
        }

        if s in current_dict:
            return current_dict[s]
        return s

    gettext.gettext = my_gettext

    import cv2 as cv
    import numpy as np
    from progressbar import ProgressBar
    from progressbar import FormatLabel
    from progressbar import Percentage
    from progressbar import Bar
    from progressbar import RotatingMarker
    from progressbar import ETA
    from itertools import chain
    from itertools import groupby
    from PIL import Image
    from Config import Config
    from tools import add_resolution_to_jpg
    from tools import pdf_count_pages
    from tools import loginfo
    from tools import logerror
    from tools import make_wide
    from show import show_results
    from pboletin_logo import logos_from_pdf

except ImportError as err:
    modulename = err.args[0].partition("'")[-1].rpartition("'")[0]
    print(_("No fue posible importar el modulo: %s") % modulename)
    sys.exit(-1)


def resource_path(relative):
    """Obtiene un path, toma en consideración el uso de pyinstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)


def init_argparse():
    """Inicializar parametros del programa."""
    cmdparser = argparse.ArgumentParser(prog=__appname__,
                                        description="%s\n%s\n" % (__appdesc__, __copyright__),
                                        epilog="",
                                        add_help=True,
                                        formatter_class=make_wide(argparse.HelpFormatter, w=80, h=42)
                                        )

    opciones = {
                "pdffile": {
                            "type": str,
                            "nargs": '?',
                            "action": "store",
                            "help": _("Boletín en PDF a procesar")
                },
                "--version -v": {
                            "action": "version",
                            "version": __version__,
                            "help":	_("Mostrar el número de versión y salir")
                },
                "--config -c": {
                            "type":	str,
                            "action": "store",
                            "dest": "configfile",
                            "default": None,
                            "help": _("Establecer el archivo de configuración del proceso de recorte. Por defecto se busca 'pboleti.ini'.")
                },
                "--debug-page -p": {
                            "type":	int,
                            "action": "store",
                            "dest":	"debug_page",
                            "default": None,
                            "help":	_("Establecer el proceso de una determinada página para debug.")
                },
                "--log-level -n": {
                            "type":	str,
                            "action": "store",
                            "dest":	"loglevel",
                            "default": "info",
                            "help":	_("Nivel de log")
                },
                "--input-path -i": {
                            "type":	str,
                            "action": "store",
                            "dest":	"inputpath",
                            "default": None,
                            "help":	_("Carpeta dónde se alojan los boletines en pdf a procesa")
                },
                "--log-file -l": {
                            "type":	str,
                            "action": "store",
                            "dest":	"logfile",
                            "default": None,
                            "help":	_("Archivo de log"),
                            "metavar": "file"
                },
                "--from-page -f": {
                            "type":	int,
                            "action": "store",
                            "dest":	"from_page",
                            "default": None,
                            "help":	_("Desde que página se procesará del PDF")
                },
                "--to-page -t": {
                            "type":	int,
                            "action": "store",
                            "dest":	"to_page",
                            "default": None,
                            "help":	_("Hasta que página se procesará del PDF")
                },
                "--quiet -q": {
                            "action": "store_true",
                            "dest":	"quiet",
                            "default": False,
                            "help":	_("Modo silencioso sin mostrar barra de progreso.")
                }
        }

    for key, val in opciones.items():
        args = key.split()
        kwargs = {}
        kwargs.update(val)
        cmdparser.add_argument(*args, **kwargs)

    return cmdparser


def crop_regions(filepath, workpath, outputpath, last_acta, metadata=None):

    filename, _ = os.path.splitext(os.path.basename(filepath))

    ############################################################################
    # El calculo de todo esta hecho sobre una base de 300 dpi
    # Hay que compensar si la resolucion es distinta
    ############################################################################
    cfg.compensation = (cfg.resolution/300)

    ############################################################################
    # Lectura inicial de la imagen
    ############################################################################
    loginfo("Abriendo archivo: {0}".format(filepath))
    src = cv.imread(filepath)
    if src is None:
        logerror('opening {0}!'.format(filepath))
        return -1

    height, width, channels = src.shape

    ############################################################################
    # Me quedo solo con el color de las lineas rectas y el texto b y n (negativo)
    ############################################################################
    loginfo("Mask image (from {0} to {1})".format(cfg.linecolor_from, cfg.linecolor_to))
    mask_bw_negative = cv.inRange(src, cfg.linecolor_from, cfg.linecolor_to)

    ############################################################################
    # Quito artefactos de hasta una cierta superficie
    ############################################################################
    loginfo("Remove artifacts")
    nb_components, output, stats, centroids = cv.connectedComponentsWithStats(mask_bw_negative, connectivity=8)
    sizes = stats[1:, -1]
    nb_components = nb_components - 1
    clean_mask = np.zeros((output.shape[0], output.shape[1], 3), dtype="uint8")

    for i in range(0, nb_components):
        if sizes[i] >= cfg.artifact_min_size*cfg.compensation:
            clean_mask[output == i + 1] = 255
    ############################################################################

    loginfo("Copy original")
    original_con_lineas = np.copy(src)
    original_original_con_lineas = np.copy(src)
    final = src

    ############################################################################
    # Engroso la máscara para no perder lineas rectas
    ############################################################################
    loginfo("Dilate")
    clean_mask_gray = cv.Canny(clean_mask, 50, 150, apertureSize=3)
    kernel = cv.getStructuringElement(cv.MORPH_CROSS, (2, 2))
    clean_mask_gray = cv.dilate(clean_mask_gray, kernel, iterations=1)

    ############################################################################
    # Detección de líneas rectas y generación de máscara de recorte
    ############################################################################
    height, width, channels = final.shape
    crop_mask = np.zeros((height, width, 3), np.uint8)
    minLineLength = int(cfg.line_min_length*cfg.compensation)
    maxLineGap = int(cfg.line_max_gap*cfg.compensation)
    theta = int(cfg.theta)
    thres = int(cfg.line_thres*cfg.compensation)
    rho = cfg.line_rho
    loginfo("Lines detection")

    linesP = None
    linesP = cv.HoughLinesP(clean_mask_gray, rho, np.pi/theta, thres, minLineLength=minLineLength, maxLineGap=maxLineGap)

    cv.imwrite(os.path.join(workpath, '01.original.png'), src)
    cv.imwrite(os.path.join(workpath, '02.mask_bw_negative.png'), mask_bw_negative)
    cv.imwrite(os.path.join(workpath, '03.clean_mask.png'), clean_mask)
    cv.imwrite(os.path.join(workpath, '04.clean_mask_gray.png'), clean_mask_gray)

    if linesP is not None:

        llorig = [e[0] for e in np.array(linesP).tolist()]
        for linea in [e[1] for e in enumerate(llorig)]:
            cv.line(original_original_con_lineas, (linea[0], linea[1]), (linea[2], linea[3]), (0, 0, 255), 3, cv.LINE_AA)

        ll = process_lines(src, llorig, cfg.resolution, cfg.only_horizontal, cfg.h_line_gap, cfg.v_line_gap, cfg.compensation)
        for linea in [e[1] for e in enumerate(ll)]:
            cv.line(original_con_lineas, (linea[0], linea[1]), (linea[2], linea[3]), (0, 0, 255), 3, cv.LINE_AA)
            cv.line(crop_mask, (linea[0], linea[1]), (linea[2], linea[3]), (0, 0, 255), 3, cv.LINE_AA)

        if cfg.save_process_files:
            cv.imwrite(os.path.join(workpath, '05.crop_mask.png'), crop_mask)
            cv.imwrite(os.path.join(workpath, '06.original_con_lineas.png'), original_con_lineas)

        ############################################################################
        # En base a la mascara obtengo los rectangulos de interes
        ############################################################################
        loginfo("Contours")
        gray = cv.cvtColor(crop_mask, cv.COLOR_BGR2GRAY)  # convert to grayscale
        retval, thresh_gray = cv.threshold(gray, thresh=1, maxval=255, type=cv.THRESH_BINARY_INV)
        contours, hierarchy = cv.findContours(thresh_gray, cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE)

        ############################################################################
        # Recorto los rectangulos
        # Si las coordenadas de algun acta entran dentro de la zona de recorte
        # Bien! podemos asociar la zona con el número de acta
        ############################################################################
        max_area = cfg.max_area * cfg.compensation
        min_area = cfg.min_area * cfg.compensation
        if metadata:
            (x, y, actas) = metadata
            relation = sum([height/y, width/x])/2

        contornos = []
        for cont in contours:
            x, y, w, h = cv.boundingRect(cont)
            area = w * h
            contornos.append((x, y, w, h, area))

        final = final.astype(np.uint8)

        contornos.sort(key=lambda x: x[4])

        i = 1
        adj = 3  # Para que no entren las líneas rectas
        for recorte in contornos[:-2]:
            x, y, w, h, area = recorte
            x = x+adj
            y = y+adj
            w = w-(adj*2)
            h = h-(adj*2)
            if area < max_area and area > min_area:

                acta = get_acta(actas, (x, y, x+w, y+h), relation)

                roi = final[y:y+h, x:x+w]
                roi = get_main_area(roi, acta)

                save_crop(acta, roi, outputpath, filename, i, last_acta)
                i = i + 1

        loginfo("End crop_regions")
        return i-1

    return 0


def get_main_area(img, acta):

    remove = cfg.remove_pixels if cfg.remove_pixels else [0, 0, 0, 0]

    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, thresh = cv.threshold(gray, 127, 255, cv.THRESH_BINARY_INV)
    kernel = np.ones((7, 7), np.uint8)
    gray = cv.dilate(thresh, kernel, iterations=1)
    ctrs, hier = cv.findContours(gray.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    areas = [(t[0], t[1], t[0]+t[2], t[1]+t[3]) for t in [cv.boundingRect(ctr) for ctr in ctrs]]
    height, width, channels = img.shape

    if not areas:
        # No hay zonas de interes posiblemente imagen en blanco
        areas = [(0, 0, width, height)]

    lmin = list(map(min, zip(*areas)))
    lmax = list(map(max, zip(*areas)))

    add = 3
    seguridad = (
        lmin[0]-add if lmin[0]-add > 0 else 0,
        lmin[1]-add if lmin[1]-add > 0 else 0,
        lmax[2]+add if lmax[2]+add < width else width,
        lmax[3]+add if lmax[3]+add < height else height
    )

    x1 = seguridad[0] if seguridad[0] < remove[0] else remove[0]
    y1 = seguridad[1] if seguridad[1] < remove[1] else remove[1]

    x2 = seguridad[2] if seguridad[2] > width-remove[2] else width-remove[2]
    y2 = seguridad[3] if seguridad[3] > height-remove[3] else height-remove[3]

    crop = (x1, y1, x2, y2)

    loginfo("Acta			  : {0}".format(acta))
    loginfo("Recorte seguridad: {0}".format(str(seguridad)))
    loginfo("Recorte final	  : {0}".format(str(crop)))

    roi = img[crop[1]:crop[1]+crop[3], crop[0]:crop[0]+crop[2]]
    return roi


def save_crop(acta, crop, outputpath, boletin, index, last_acta):

    loginfo("save_crop")

    unique_colors = len(np.unique(crop.reshape(-1, crop.shape[2]), axis=0))
    compression = [int(cv.IMWRITE_JPEG_QUALITY), cfg.jpg_compression]
    fmerged = None

    if unique_colors <= 1:
        return 0

    if not acta and last_acta:
        loginfo("merging")

        ############################################################################################
        # Es un Merged
        ############################################################################################
        ext_compat = [e for e in cfg.imgext if e not in ['pcx']][0]

        last_file = os.path.join(outputpath, ext_compat, '{0}.{1}'.format(last_acta, ext_compat))
        last_img = cv.imread(last_file)

        max_width = 0     # find the max width of all the images
        total_height = 0  # the total height of the images (vertical stacking)
        images = [last_img, crop]
        for img in images:
            if img.shape[1] > max_width:
                max_width = img.shape[1]
            total_height += img.shape[0]

        merged = np.zeros((total_height, max_width, 3), dtype=np.uint8)
        merged.fill(255)

        current_y = 0  # keep track of where your current image was last placed in the y coordinate
        for image in images:
            merged[current_y:image.shape[0] + current_y, :image.shape[1], :] = image
            current_y += image.shape[0]

        unique_colors = len(np.unique(merged.reshape(-1, merged.shape[2]), axis=0))

        for ext in cfg.imgext:
            # shutil.move(last_file, os.path.join(outputpath, ext, 'check'))

            fmerged = os.path.join(outputpath, ext, 'check', '{0}.merged.{1}'.format(last_acta, ext))

            if ext.lower() == 'pcx':
                # Mejorar esto por Dios
                src = fmerged.replace(ext, cfg.imgext[0])
                Image.open(src).save(fmerged)
            else:
                if unique_colors <= 256:
                    merged = cv.cvtColor(merged, cv.COLOR_BGR2GRAY)

                loginfo("Saving           : {0}".format(fmerged))
                if ext.lower() == 'jpg':
                    cv.imwrite(fmerged, merged, compression)
                    add_resolution_to_jpg(fmerged, cfg.resolution)
                else:
                    cv.imwrite(fmerged, merged, compression)

    for ext in cfg.imgext:
        opath = os.path.join(outputpath, ext)
        if acta:
            f = os.path.join(opath, '{0}.{1}'.format(acta, ext))
        else:
            f = os.path.join(opath, 'check', '{0}_crop_{1}.{2}'.format(boletin, index, ext))

        loginfo("Saving           : {0}".format(f))
        if ext.lower() == 'pcx':
            # Mejorar esto por Dios
            src = f.replace(ext, cfg.imgext[0])
            Image.open(src).save(f)
        else:
            if unique_colors <= 256:
                crop = cv.cvtColor(crop, cv.COLOR_BGR2GRAY)

            if ext.lower() == 'jpg':
                cv.imwrite(f, crop, compression)
                add_resolution_to_jpg(f, cfg.resolution)
            else:
                cv.imwrite(f, crop, compression)

    if fmerged:
        for ext in cfg.imgext:
            last_file = os.path.join(outputpath, ext, '{0}.{1}'.format(last_acta, ext))
            # Muevo el file anterior a check
            outpath = os.path.join(outputpath, ext, 'check')

            dst_filename = os.path.join(outpath, os.path.basename(last_file))
            loginfo("Moving           : {0} to {1}".format(last_file, dst_filename))
            shutil.move(last_file, outpath)

            fmerged = os.path.join(outputpath, ext, 'check', '{0}.merged.{1}'.format(last_acta, ext))
            dst_filename = os.path.join(outpath, os.path.basename(fmerged))

            loginfo("Moving           : {0} to {1}".format(fmerged, dst_filename))
            shutil.move(fmerged, last_file)

    return 1


def get_acta(actas_boletin, region_donde_buscar, relacion_aspecto):
    """get_acta: obtiene el número de acta dada una región

    Dada una región expresada en coordenadas x1, y1, x2, y2
    se trata de ubicar el número de acta que correspondería. Los números
    de acta se definen dentro del PDF también con coordenadas de la
    página.

    Args:
        actas_boletin: Lista completa de actas del boletín
        region_a_buscar: Region del recorte
        relacion_aspecto: Relación de aspecto de la página Alto/Ancho

    Returns:
        El número de acta, en caso de no encontralo None
    """

    rx1, ry1, rx2, ry2 = region_donde_buscar
    for x, y, numero in actas_boletin:
        if x*relacion_aspecto >= rx1 \
            and x*relacion_aspecto <= rx2 \
            and y*relacion_aspecto >= ry1 \
            and y*relacion_aspecto <= ry2:
            return numero

    return None


def process_lines(img, lista, in_res, only_horizontal, h_line_gap, v_line_gap, compensation):

    ############################################################################
    # Ajustamos inclinaciones de las líneas
    ############################################################################
    for linea in lista:
        linea[0] = linea[2] if abs(linea[0] - linea[2]) <= 3 else linea[0]
        linea[1] = linea[3] if abs(linea[1] - linea[3]) <= 3 else linea[1]

    verticales = [linea for linea in lista if linea[0] == linea[2]]
    horizontales = [linea for linea in lista if linea[1] == linea[3]]

    xs = list(chain(*[(linea[0], linea[2]) for linea in horizontales]))
    ys = list(chain(*[(linea[1], linea[3]) for linea in horizontales]))

    min_x = min(xs) - 10
    max_x = max(xs) + 10
    min_y = min(ys)
    max_y = max(ys)

    ############################################################################
    # Resolver el problema de falta de linea horizontal al final
    ############################################################################
    bottom = int(3300*(in_res/300))

    dif = bottom-max_y
    max_y = max_y if dif <= 50 else bottom

    ############################################################################
    # Horizontales cercanas al bottom
    ############################################################################
    for i, l in enumerate(horizontales):
        dif = bottom - l[1]
        if dif <= 50:
            horizontales[i][1] = bottom
            horizontales[i][3] = bottom

    newlista = horizontales
    newlista.extend(verticales)

    ############################################################################
    # Bajo el recorte del top
    ############################################################################
    for i, e in enumerate(newlista):
        newlista[i][1] = min_y+10 if e[1] == min_y else e[1]
        newlista[i][3] = min_y+10 if e[3] == min_y else e[3]

    min_y = min_y + 10

    ############################################################################
    # Dejar solo horizontales
    ############################################################################
    if only_horizontal:
        newlista = [linea for linea in newlista if linea[1] == linea[3]]

    ############################################################################
    # Agrego un recuadro
    ############################################################################
    newlista.append([min_x, min_y, max_x, min_y])
    newlista.append([min_x, min_y, min_x, max_y])
    newlista.append([min_x, max_y, max_x, max_y])
    newlista.append([max_x, max_y, max_x, min_y])

    ############################################################################
    # Simplificación de líneas
    ############################################################################
    newlista = simplificar(simplificar(newlista, pair=1), pair=2)
    newlista = list(map(list, set(map(tuple, newlista))))

    ############################################################################
    # Conectar lineas horizontales con las verticales
    ############################################################################
    newlista = conectar_horizontales(newlista, int(h_line_gap*compensation))
    newlista = conectar_verticales(newlista, int(v_line_gap*compensation))

    return(newlista)


def simplificar(mylista, pair, level=5):

    xs = list(chain(*[(linea[pair-1], linea[pair+1]) for linea in mylista]))
    xs.sort()

    lista = []
    grupo = 0
    for i, p in enumerate(xs):
        if i > 0:
            if p - (xs[i-1]) <= level:
                lista.append((p, lista[i-1][1]))
            else:
                grupo = grupo + 1
                lista.append((p, grupo))
        else:
            grupo = 1
            lista.append((p, grupo))

    px = dict(lista)
    aprox = {}
    for key, group in groupby(lista, key=lambda x: x[1]):
        aprox[key] = statistics.median_low(i for i, j in group)

    newlist = mylista[:]

    if pair == 1:
        for i, e in enumerate(newlist):
            newlist[i] = [aprox[px[e[0]]], e[1], aprox[px[e[2]]], e[3]]
    else:
        for i, e in enumerate(newlist):
            newlist[i] = [e[0], aprox[px[e[1]]], e[2], aprox[px[e[3]]]]

    return newlist


def conectar_horizontales(mylista, level=50):

    verticales = [linea for linea in mylista if linea[0] == linea[2]]
    verticales.sort(key=lambda x: abs(x[3]-x[1]))  # Ordeno ascendente, para que valgan los más largos

    horizontales = [linea for linea in mylista if linea[1] == linea[3]]

    xvert = {}
    for i in [linea[0] for linea in verticales]:
        for j in range(0, level):
            xvert[i+j] = i
            xvert[i-j] = i

    for i, l in enumerate(horizontales):
        horizontales[i][0] = xvert.get(horizontales[i][0], horizontales[i][0])
        horizontales[i][2] = xvert.get(horizontales[i][2], horizontales[i][2])

    horizontales.extend(verticales)
    return horizontales


def conectar_verticales(mylista, level=50):

    newlist = mylista[:]
    verticales = [linea for linea in mylista if linea[0] == linea[2]]
    horizontales = [linea for linea in mylista if linea[1] == linea[3]]
    yvert = {}
    for i in [linea[1] for linea in horizontales]:
        for j in range(0, level):
            yvert[i+j] = i
            yvert[i-j] = i

    for i, l in enumerate(verticales):
        verticales[i][1] = yvert.get(verticales[i][1], verticales[i][1])
        verticales[i][3] = yvert.get(verticales[i][3], verticales[i][3])

    return newlist


def get_metadata(cfg, html):
    """get_metadata: extrae información del boletin en el PDF

    El boletin convertido de PDF -> HTML, se procesa con patrones
    regulares configurables en el INI para exxtraer la información
    necesaria de la página procesada:
        - Tamaño x, y de la página
        - # acta
        - Posición x,y del # acta en la página

    Args:
        html(str): Cadena completa html de la página a procesar.

    """

    x, y = 1, 1
    rxactas = re.compile(cfg.rxpagedim, re.MULTILINE)
    t = re.findall(rxactas, html)
    if t:
        x, y = map(int, t[0])


    rxactas = re.compile(cfg.rxactas, re.MULTILINE)
    m = re.finditer(rxactas, html)

    if m:
        return (x, y, list((int(e.group(2)), int(e.group(1)), e.group(3).replace('.', '')) for e in m))
    else:
        return None


def process_pdf(cfg, pdf_file, quiet=False):

    lista_actas = []
    total_actas = 0
    total_regions = 0
    total_pages = pdf_count_pages(pdf_file, cfg.pdfinfo_bin, cfg.rxcountpages)

    print("\nRecorte de actas\n")

    loginfo("{0} has {1} pages".format(pdf_file, total_pages))

    if not cfg.debug_page:
        firstp = cfg.from_page if cfg.from_page else (cfg.ignore_first_pages+1)
        endp = cfg.to_page if cfg.to_page else (total_pages-cfg.ignore_last_pages)+1

        if cfg.detect_export_pages and (not cfg.from_page and not cfg.to_page):
            firstp = 1
            endp = total_pages

        num_bars = (endp - firstp) + 1
    else:
        firstp = cfg.debug_page
        endp = cfg.debug_page
        num_bars = 1

    if not quiet:
        widgets = [FormatLabel(''), ' ', Percentage(), ' ', Bar('#'), ' ', ETA(), ' ', RotatingMarker()]
        bar = ProgressBar(widgets=widgets, maxval=num_bars)

    loginfo("Create temp dir")
    workpath = tempfile.mkdtemp()

    filename, _ = os.path.splitext(os.path.basename(pdf_file))
    outputpath = os.path.join(cfg.outputdir, filename)
    loginfo("Create outputp dir")
    os.makedirs(outputpath, exist_ok=True)

    loginfo("Extract PDF pages form {0}".format(pdf_file))
    maxz = len(str(total_pages))
    i = 1

    ############################################################################
    # Creamos las subcarpetas para guardar las imagenes por extensión
    ############################################################################
    for ext in cfg.imgext:
        opath = os.path.join(outputpath, ext, "check")
        os.makedirs(opath, exist_ok=True)

    for p in range(firstp, endp+1):

        loginfo("Extract page {0} of {1}".format(i, num_bars))
        if cfg.export_logos:
            cmdline = '{0} -png -q -f {3} -l {4} {1} {2}/pagina-{5}'.format(
                cfg.pdfimages_bin,
                pdf_file,
                workpath,
                p,
                p,
                p
            )
            loginfo(cmdline)
            with subprocess.Popen(cmdline, shell=True) as _:
                pass

        cmdline = '{0} -q -png -f {3} -l {4} -r {5} {1} {2}/pagina'.format(
            cfg.pdftoppm_bin,
            pdf_file,
            workpath,
            p,
            p,
            cfg.resolution
        )
        loginfo(cmdline)
        with subprocess.Popen(cmdline, shell=True) as _:
            pass

        cmdline = '{0} -q -c -f {3} -l {4} {1} {2}/pagina'.format(
            cfg.pdftohtml_bin,
            pdf_file,
            workpath,
            p,
            p
        )
        loginfo(cmdline)
        with subprocess.Popen(cmdline, shell=True) as _:
            pass

        with open(os.path.join(workpath, 'pagina-{0}.html'.format(str(p))), 'r', encoding="Latin1") as f:
            html = f.read()

        img_file = "pagina-{0}.png".format(str(p).zfill(maxz))
        img_file = os.path.join(workpath, img_file)
        actas = get_metadata(cfg, html)
        loginfo("Actas encontradas: {0}".format(str(actas)))

        if not cfg.detect_export_pages or (cfg.detect_export_pages and len(actas[2]) > 0):

            last_acta = lista_actas[-1] if lista_actas else None

            actas_pagina = [a[2] for a in actas[2]]
            lista_actas.extend(actas_pagina)
            total_actas = total_actas + (len(actas[2]) if actas is not None else 0)

            try:
                total_regions = total_regions + crop_regions(img_file,
                                                             workpath,
                                                             outputpath,
                                                             last_acta=last_acta,
                                                             metadata=actas)

            except Exception as msg:
                logerror("Error:" + str(msg))

            if not quiet:
                widgets[0] = FormatLabel('[Página {0} de {1}]'.format(i, num_bars))

        if not quiet:
            bar.update(i)

        i = i + 1

    loginfo("Remove temp dir")

    if not quiet:
        bar.finish()

    printmsg = True if not quiet else False

    loginfo("", printmsg=True)
    loginfo("-- Estatus -------------------------------------------", printmsg=printmsg)
    loginfo("Carpeta temporal de trabajo  : {0}".format(workpath), printmsg=printmsg)
    loginfo("Carpeta de salida            : {0}".format(outputpath), printmsg=printmsg)

    if not cfg.debug_page:
        loginfo("Eliminamos carpeta de trabajo")
        shutil.rmtree(workpath)

    actas_error = []
    for a in lista_actas:
        f = os.path.join(outputpath, cfg.imgext[0], '{0}.{1}'.format(a, cfg.imgext[0]))
        if not os.path.isfile(f):
            actas_error.append(a)

    loginfo("Total de actas               : {0}".format(total_actas), printmsg=True)
    loginfo("Total de regiones recortadas : {0}".format(total_regions), printmsg=True)
    if actas_error:
        loginfo("Actas no encontradas         : {0}".format(",".join(actas_error)), printmsg=True)

    if not cfg.debug_page:
        # loginfo("Actas encontradas            : {0}".format(",".join(set(lista_actas)-set(actas_error))), printmsg=True)
        loginfo("-- Configuración -------------------------------------", printmsg=True)
        for linea in str(cfg).split("\n"):
            loginfo(linea, printmsg=True)

    loginfo("------------------------------------------------------", printmsg=True)
    loginfo("Finish process", printmsg=True)

    if cfg.debug_page:
        show_results(workpath, outputpath, lista_actas)


################################################################################
#  Cuerpo principal
################################################################################
if __name__ == "__main__":

    cfg = Config()

    cmdparser = init_argparse()
    try:
        args = cmdparser.parse_args()

    except IOError as msg:
        cmdparser.error(str(msg))
        sys.exit(-1)

    # Definir el path de dónde obtener la configuración
    if not args.configfile:
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)

        configfile = resource_path(os.path.join(application_path, 'pboletin.ini'))
    else:
        configfile = args.configfile

    if args.pdffile:

        if args.logfile:
            log_level = getattr(logging, args.loglevel.upper(), None)
            logging.basicConfig(filename=args.logfile,
                                level=log_level,
                                format='%(asctime)s|%(levelname)s|%(message)s',
                                datefmt='%Y/%m/%d %I:%M:%S',
                                filemode='w')

        try:
            loginfo("Config file: {0}".format(configfile))
            cfg.set_file(configfile)
        except IOError as msg:
            cmdparser.error(str(msg))
            sys.exit(-1)

        if args.debug_page:
            cfg.save_process_files = True
            cfg.debug_page = args.debug_page

        cfg.from_page = args.from_page
        cfg.to_page = args.to_page
        if args.inputpath:
            cfg.inputdir = args.inputpath

        args.pdffile = os.path.join(cfg.inputdir, args.pdffile)
        loginfo("Process PDF : {0}".format(args.pdffile))

        if os.path.isfile(args.pdffile):

            if cfg.export_logos:
                logos_from_pdf(cfg, args.pdffile, args.quiet)

            process_pdf(cfg, args.pdffile, args.quiet)

        else:
            logerror("No existe el archivo " + args.pdffile)

    else:
        cmdparser.print_help()
