pyinstaller pboletin.py --noupx
cp pboletin.plus.ini dist/pboletin/pboletin.ini
cp tools/pdftools/ dist/pboletin/ -r
cp tools/procesar.bat dist/*
