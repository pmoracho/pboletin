# pboletin - Procesamiento de boletines del INPI

**pboletin** es una herramienta que procesa los boletines de marcas del INPI,
generando recortes de imágenes asociadas a cada acta. Básicamente se leen todas
las páginas de un Boletín en PDF y se generan recortes gráficos en varios
formatos para cada número de acta del boletín.


# Empecemos

Antes que nada, necesitaremos:

* [Git for Windows](https://git-scm.com/download/win) instalado y funcionando
* Una terminal de Windows, puede ser `cmd.exe`

Con **Git** instalado, desde la línea de comando y con una carpeta dónde
alojaremos este proyecto, por ejemplo `c:\proyectos`, simplemente:

``` 
c:\> c: 
c:\> cd \Proyectos 
c:\> git clone <url del repositorio>
c:\> cd <carpeta del proyecto>
``` 

| ------------- |:--------------|
| Repositorio   | https://github.com/pmoracho/pboletin.git |
| Carpeta del proyecto   | . |


## Instalación de **Python**

Para desarrollo de la herramienta es necesario, en primer término, descargar un
interprete Python. **pboletin** ha sido desarrollado con la versión 3.6, no es
mala idea usar esta versión, sin embargo debiera funcionar perfectamente bien
con cualquier versión de la rama 3x.

**Importante:** Si bien solo detallamos el procedimiento para entornos
**Windows**, el proyecto es totalmente compatible con **Linux**

* [Python 3.6.6 (32 bits)](https://www.python.org/ftp/python/3.6.6/python-3.6.6.exe)
* [Python 3.6.6 (64 bits)](https://www.python.org/ftp/python/3.6.6/python-3.6.6-amd64.exe)

Se descarga y se instala en el sistema el interprete **Python** deseado. A
partir de ahora trabajaremos en una terminal de Windows (`cmd.exe`). Para
verificar la correcta instalación, en particular que el interprete este en el `PATH`
del sistemas, simplemente corremos `python --version`, la salida deberá
coincidir con la versión instalada 

Es conveniente pero no mandatorio hacer upgrade de la herramienta pip: `python
-m pip install --upgrade pip`

## Instalación de `Virtualenv`

[Virutalenv](https://virtualenv.pypa.io/en/stable/). Es la herramienta estándar
para crear entornos "aislados" de **Python**. En nuestro ejemplo **pboletin**,
requiere de Python 3x y de varios "paquetes" adicionales de versiones
específicas. Para no tener conflictos de desarrollo lo que haremos mediante
esta herramienta es crear un "entorno virtual" en una carpeta del proyecto (que
llamaremos `venv`), dónde una vez "activado" dicho entorno podremos instalarle
los paquetes que requiere el proyecto. Este "entorno virtual" contendrá una
copia completa de **Python** y los paquetes mencionados, al activarlo se
modifica el `PATH` al `python.exe` que ahora apuntará a nuestra carpeta del
entorno y nuestras propias librerías, evitando cualquier tipo de conflicto con un
entorno **Python** ya existente. La instalación de `virtualenv` se hará
mediante:

```
c:\> pip install virtualenv
```

## Creación y activación del entorno virtual

La creación de nuestro entorno virtual se realizará mediante el comando:

```
C:\Proyectos\pboletin> virtualenv venv --clear --prompt=[pboletin] --no-wheel
```

Para "activar" el entorno simplemente hay que correr el script de activación
que se encontrará en la carpeta `./venv/Scripts` (en linux sería `.\venv\bin`)

```
C:\Proyectos\pboletin> .\venv\Scripts\activate.bat
[pboletin] C:\Proyectos\pboletin>
```

Como se puede notar se ha cambiado el `prompt` con la indicación del entorno
virtual activo, esto es importante para no confundir entornos si trabajamos con
múltiples proyecto **Python** al mismo tiempo.

## Instalación de requerimientos

Mencionábamos que este proyecto requiere varios paquetes adicionales, la lista
completa está definida en el archivo `requirements.txt` para instalarlos en
nuestro entorno virtual, simplemente:

```
[pboletin] C:\Proyectos\pboletin> pip install -r requirements.txt
```

## Desarrollo

Si todos los pasos anteriores fueron exitosos, podríamos verificar si la
aplicación funciona correctamente mediante:

```
[pboletin] C:\Proyectos\pboletin>python pboletin.py
uso: pboletin [-h] [--version] [--config CONFIGFILE] [--debug-page DEBUG_PAGE]
              [--log-level LOGLEVEL] [--input-path INPUTPATH]
              [--log-file file] [--from-page FROM_PAGE] [--to-page TO_PAGE]
              [--quiet]
              [pdffile]

Procesamiento de boletines (c) 2018, Patricio Moracho <pmoracho@gmail.com>

argumentos posicionales:
  pdffile                                 Boletín en PDF a procesar

argumentos opcionales:
  -h, --help                              mostrar esta ayuda y salir
  --version, -v                           Mostrar el número de versión y salir
  --config CONFIGFILE, -c CONFIGFILE      Establecer el archivo de
                                          configuración del proceso de
                                          recorte. Por defecto se busca
                                          'pboleti.ini'.
  --debug-page DEBUG_PAGE, -p DEBUG_PAGE  Establecer el proceso de una
                                          determinada página para debug.
  --log-level LOGLEVEL, -n LOGLEVEL       Nivel de log
  --input-path INPUTPATH, -i INPUTPATH    Carpeta dónde se alojan los
                                          boletines en pdf a procesa
  --log-file file, -l file                Archivo de log
  --from-page FROM_PAGE, -f FROM_PAGE     Desde que página se procesará del
                                          PDF
  --to-page TO_PAGE, -t TO_PAGE           Hasta que página se procesará del
                                          PDF
  --quiet, -q                             Modo silencioso sin mostrar barra de
                                          progreso.

```

La ejecución sin parámetros arrojará la ayuda de la aplicación. A partir de
aquí podríamos empezar con la etapa de desarrollo.

## Generación del paquete para deploy

Para distribuir la aplicación en entornos **Windows** nos apoyaremos en
**Pyinstaller**, un modulo, instalado junto a los requerimientos, que nos
permite crear una carpeta de distribución de la aplicación totalmente portable.
Simplemente deberemos ejecutar el archivo `windist.bat`, al finalizar el
procesos deberías contar con una carpeta en `.\dist\pboletin` la cual será una
instalación totalmente portable de la herramienta, no haría falta nada más que
copiar la misma al equipo o servidor desde dónde deseamos ejecutarla.


