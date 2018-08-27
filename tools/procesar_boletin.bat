@echo off
set /p boletin="Numero de boletin a procesar: "
@pboletin.exe %boletin%.pdf

@copy \\Momdb2Test\Marcas\PruebasNip\%boletin%\JPG\*.JPG \\PlusDesa02\Mecanus\PI\Images\Import\Boletin\
@copy \\Momdb2Test\Marcas\PruebasNip\%boletin%\PCX\*.PCX \\PlusDesa02\Mecanus\PI\Images\Import\Boletin\


pause