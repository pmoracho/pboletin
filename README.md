<M-F9>
# pboletin - Procesamiento de boletines del INPI

Herramienta para recorte automático de las marcas publicadas por el INPI


**pboletin** es una herramienta que procesa los boletines de marcas del INPI,
generando recortes de imagenes asociadas a cada acta. Básicamente se leen todas
las páginas de un Boletín en PDF y se generan recortes gráficos en varios
formatos para cada número de acta del boletín.


# Empecemos


## Instalación de Python

Para desarrollo de la herramienta es necesario, en primer término, descargar un
interprete Python. **pboletin** ha sido desarrollado con la versión 3.5, no es
mala idea usar esta versión, sin embargo debiera funcionar perfectamente bien
con cualquier versión de la rama 3x.

**Importante:** Si bien solo detallamos el procedimiento para entornos
**Windows**, el proyecto es totalmente compatible con **Linux**

* [Python 3.5 (32 bits)](https://www.python.org/ftp/python/3.5.4/python-3.5.4.exe)
* [Python 3.5 (64 bits)](https://www.python.org/ftp/python/3.5.4/python-3.5.4rc1-amd64.exe)

Se descarga y se instala en el sistema el interprete **Python** deseado. A
partir de ahora trabajaremos en una terminal de windows (`cmd.exe`). Para
verificar la correcta instalación, en particular que el interprete este en el `PATH`
del sistemas, simplemente corremos `python --version`, la salida deberá
coincidir con la versión instalada 

Es conveniente pero no mandatorio hacer upgrade de la herramienta pip: `python
-m pip install --upgrade pip`

## Instalación de `Virtualenv`

[Virutalenv](https://virtualenv.pypa.io/en/stable/). Es la herramienta
estándar para crear entornos "aislados" de **Python**. En nuestro ejemplo
**pboletin**, requiere de Ptython 3.5 y de varios "paquetes" adcionales de
versiones específicas. Para no tener conflictos de desarrollo lo que haremos
mediante esta herramienta es crear un "entorno virtual" en una
carpeta del projecto (que llamaremos `venv`), dónde una vez "activado" dicho entorno podremos
instalarle los paquetes que requiere el proyecto. Este "entorno virtual"
contendrá una copia completa de **Python** y los paquetes mencionados, al
activarlo se modifica el `PATH` a `python.exe` que ahora apuntará a nuestra
carpeta del entorno y nuestras propias librerí, evitando cualquier tipo de
conflicto con un entorno **Python** ya existente. La instalación de `virtualenv` se
hara mediante 

```
pip install virtualenv
```

* Creación y activación del entorno virtual


* Instalación de requrimientos

* Desarrollo

* Generación del paquete para deploy

