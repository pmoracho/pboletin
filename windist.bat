@echo off

REM --------------------------------------------------------
REM Bat para la generación del paquete de deploy de pboletin
REM --------------------------------------------------------


REM --------------------------------------------------------
REM Creación del paquete para distribuir
REM --------------------------------------------------------
@echo --------------------------------------------------------
@echo Generando distribucion con pyinstaller..
@echo --------------------------------------------------------
@pyinstaller pboletin.py --onedir --noupx --clean --noconfirm

@echo --------------------------------------------------------
@echo Copiando archivos y herramientas adicionales..
@echo --------------------------------------------------------

REM --------------------------------------------------------
REM Ini de la applicación
REM !! Copiar manualmente si es necesario
REM --------------------------------------------------------
REM @copy pboletin.ini dist\pboletin\pboletin.ini

REM --------------------------------------------------------
REM Carpeta de pdftools
REM --------------------------------------------------------
@mkdir dist\pboletin\pdftools
@copy tools\pdftools\* dist\pboletin\pdftools
@copy tools\procesar_boletin.bat dist\pboletin

REM --------------------------------------------------------
REM Eliminar archivos de trabajo
REM --------------------------------------------------------
@echo --------------------------------------------------------
@echo Eliminando archivos de trabajo ..
@echo --------------------------------------------------------
@rmdir build /S /Q
@del *.spec /S /F /Q

@echo --------------------------------------------------------
@echo Carpeta a distribuir dist\pboletin..
@echo --------------------------------------------------------
