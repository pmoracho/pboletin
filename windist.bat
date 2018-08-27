REM --------------------------------------------------------
REM Bat para la generación del paquete de deploy de pboletin
REM --------------------------------------------------------

@echo off

REM --------------------------------------------------------
REM Creación del paquete para distribuir
REM --------------------------------------------------------
@echo Generando distribucion con pyinstaller..
@pyinstaller pboletin.py --onedir --noupx --clean --noconfirm

@echo Copiando archivos y herramientas adicionales..

REM --------------------------------------------------------
REM Ini de la applicación
REM --------------------------------------------------------
@copy pboletin.ini dist\pboletin\pboletin.ini

REM --------------------------------------------------------
REM Carpeta de pdftools
REM --------------------------------------------------------
@mkdir dist\pboletin\pdftools
@copy tools\pdftools\* dist\pboletin\pdftools
@copy tools\procesar_boletin.bat dist\pboletin

REM --------------------------------------------------------
REM Eliminar archivos de trabajo
REM --------------------------------------------------------
@echo Eliminando archivos de trabajo ..
@del build /S /F /Q
@del *.spec /S /F /Q

@echo Carpeta a distribuir dist\pboletin..