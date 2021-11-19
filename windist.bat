@echo off

@echo  --------------------------------------------------------
@echo Bat para la generación del paquete de deploy de pboletin
@echo --------------------------------------------------------


@echo --------------------------------------------------------
@echo Creación del paquete para distribuir
@echo --------------------------------------------------------
@echo --------------------------------------------------------
@echo Generando distribucion con pyinstaller..
@echo --------------------------------------------------------
@pyinstaller pboletin.py --onedir --noupx --clean --noconfirm --path=".venv\lib\site-packages\cv2"


@echo --------------------------------------------------------
@echo Copiando archivos y herramientas adicionales..
@echo --------------------------------------------------------

@echo --------------------------------------------------------
@echo Ini de la applicación
@echo --------------------------------------------------------
@copy pboletin.win.ini dist\pboletin\pboletin.ini

@echo --------------------------------------------------------
@echo Carpeta de pdftools y procesar_boletib.bat
@echo --------------------------------------------------------
@mkdir dist\pboletin\pdftools
@copy tools\pdftools\* dist\pboletin\pdftools
@copy tools\procesar_boletin.bat dist\pboletin

@echo --------------------------------------------------------
@echo Eliminar archivos de trabajo
@echo --------------------------------------------------------
@echo --------------------------------------------------------
@echo Eliminando archivos de trabajo ..
@echo --------------------------------------------------------
@rmdir build /S /Q
@del *.spec /S /F /Q

@echo --------------------------------------------------------
@echo Carpeta a distribuir dist\pboletin..
@echo --------------------------------------------------------
