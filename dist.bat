pyinstaller pboletin.py --onedir --noupx --clean --noconfirm
cp pboletin.plus.ini dist/pboletin/pboletin.ini
cp tools/pdftools/ dist/pboletin/ -r
cp tools/procesar_boletin.bat dist/*
rm -r build
rm *.spec
