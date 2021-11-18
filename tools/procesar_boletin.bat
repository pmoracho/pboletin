@echo off
set /p boletin="Numero de boletin a procesar: "
@pboletin.exe %boletin%.pdf

@copy F:\PI_import\pdftxt\cd\out\%boletin%\JPG\*.JPG F:\PI_import\pdftxt\cd\Boletin
@copy F:\PI_import\pdftxt\cd\out\%boletin%\PCX\*.PCX F:\PI_import\pdftxt\cd\Boletin


pause