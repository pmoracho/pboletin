#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Patricio Moracho <pmoracho@gmail.com>
#
# pboletin_logo.py
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
pboletin_logo
=============

Extracción de textos e imagenes de los PDF de marcas
"""

__author__ = "Patricio Moracho <pmoracho@gmail.com>"
__appname__ = "pboletin_logo"
__appdesc__ = "Procesamiento de boletines"
__license__ = 'GPL v3'
__copyright__ = "(c) 2020, %s" % (__author__)
__version__ = "1.0"
__date__ = "2020/07/07"


try:

    import gettext
    from gettext import gettext as _

    def my_gettext(s):
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

    import argparse
    import logging
    import os
    import re
    import shutil
    import sys
    import tempfile
    from pdf_content_extractor import save_image
    from progressbar import ProgressBar
    from progressbar import FormatLabel
    from progressbar import Percentage
    from progressbar import Bar
    from progressbar import RotatingMarker
    from progressbar import ETA
    from Config import Config
    from tools import loginfo
    from tools import logerror
    from tools import resource_path
    from tools import make_wide

    from pdfminer.layout import LAParams, LTTextBox, LTFigure, LTImage
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfinterp import PDFResourceManager
    from pdfminer.pdfinterp import PDFPageInterpreter
    from pdfminer.converter import PDFPageAggregator

except ImportError as err:
    modulename = err.args[0].partition("'")[-1].rpartition("'")[0]
    print(_("No fue posible importar el modulo: %s") % modulename)
    sys.exit(-1)


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
                            "help": _("Establecer el archivo de configuración del proceso de recorte. Por defecto se busca 'pboleti.ini' en la carpeta actual.")
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
                            "help":	_("Carpeta dónde se alojan los boletines en pdf a procesar")
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


class DataExtractor:

    def __init__(self, workpath):
        self.patron_acta = re.compile(r'Acta (\d+)\s', re.MULTILINE)
        self.workpath = workpath

    def get_numero_acta(self, text):
        try:
            return [int(e.group(1)) for e in re.finditer(self.patron_acta, text)][0]
        except Exception:
            None

    def get_data_from_layout(self, layout):

        texto_actas = []
        imagenes_actas = []
        for lobj in layout:

            if isinstance(lobj, LTTextBox):
                x, y, text = lobj.bbox[0], lobj.bbox[3], lobj.get_text()
                acta = self.get_numero_acta(text)
                texto_actas.append((acta, x, y, text))

            if isinstance(lobj, LTFigure):
                for n, img in enumerate(lobj, start=1):
                    if isinstance(img, LTImage):
                        x, y, filename = lobj.bbox[0], lobj.bbox[3], save_image(img, self.workpath)
                        imagenes_actas.append((x, y, filename))

        objetos = []
        texto_actas = sorted(texto_actas, key=lambda x: x[1], reverse=True)

        for xi, yi, filename in imagenes_actas:
            for acta, xt, yt, text in [e for e in texto_actas if e[0]]:
                if yt <= yi:
                    objetos.append((acta, text, filename))
                    break

        for acta, xt, yt, text in [e for e in texto_actas if e[0]]:
            if acta not in [a[0] for a in objetos]:
                objetos.append((acta, text, None))

        return objetos


def logos_from_pdf(cfg, pdf_file, quiet=False):
    """logos_from_pdf
    Procesa un archivo PDF de boletines de Marcas para extraer logos y textos de cada acta

    cfg: <Config> Objeto de congiguracón del proceso
    pdf_file: <str> path al archivo PDF del boletín
    """
    print("\nExtracción de logos y textos\n")
    workpath = tempfile.mkdtemp()

    filename, _ = os.path.splitext(os.path.basename(pdf_file))
    outputpath_logos = os.path.join(cfg.outputdir, filename, "logos")
    outputpath_txt = os.path.join(cfg.outputdir, filename, "txt")
    os.makedirs(outputpath_txt, exist_ok=True)
    os.makedirs(outputpath_logos, exist_ok=True)

    dte = DataExtractor(workpath)

    total_logos, total_textos = 0, 0
    with open(pdf_file, 'rb') as fp:

        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pages = list(PDFPage.get_pages(fp))
        total_pages = len(pages)
        loginfo("Total de páginas    : {0}".format(total_pages))

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
        i = 1

        for page in [p for n, p in enumerate(pages, start=1) if n >= firstp and n <= endp]:
            interpreter.process_page(page)
            layout = device.get_result()

            objetos = dte.get_data_from_layout(layout)
            total_logos = total_logos + len([e for e in objetos if e[2] is not None])
            total_textos = total_textos + len(objetos)
            for acta, texto, filename in objetos:
                if filename:
                    _, file_extension = os.path.splitext(filename)
                    shutil.copyfile(filename, os.path.join(outputpath_logos, "{0}{1}".format(acta, file_extension)))

                txt_file = os.path.join(outputpath_txt, "{0}.{1}".format(acta, "txt"))

                with open(txt_file, 'w', errors="ignore") as f:
                    f.write(texto)

            if not quiet:
                widgets[0] = FormatLabel('[Página {0} de {1}]'.format(i, total_pages))
                bar.update(i)
            i = i + 1

        if not quiet:
            bar.finish()

    printmsg = True if not quiet else False
    loginfo("", printmsg=printmsg)
    loginfo("-- Estatus -------------------------------------------", printmsg=printmsg)
    loginfo("Carpeta temporal de trabajo  : {0}".format(workpath), printmsg=printmsg)
    loginfo("Total de logos extraídos     : {0}".format(total_logos), printmsg=printmsg)
    loginfo("Total de textos extraídos    : {0}".format(total_textos), printmsg=printmsg)

    if not cfg.debug_page:
        loginfo("Eliminamos carpeta de trabajo")
        shutil.rmtree(workpath)


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
            loginfo("Configuración       : {0}".format(configfile))
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
        loginfo("PDF a procesar      : {0}".format(args.pdffile))

        if os.path.isfile(args.pdffile):
            logos_from_pdf(cfg, args.pdffile, args.quiet)
        else:
            logerror("No existe el archivo " + args.pdffile)

    else:
        cmdparser.print_help()
