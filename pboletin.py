import sys
import math
import cv2 as cv
import numpy as np
import glob
from operator import itemgetter
import pprint
import itertools
import os

def detect_lines(filepath):

	filename, _ = os.path.splitext(os.path.basename(filepath))

	############################################################################
	# Lectura inicial de la imagen
	############################################################################
	src = cv.imread(filepath)
	if src is None:
		print ('Error opening {0}!'.format(filepath))
		return -1

	############################################################################
	# Me quedo solo con el color de las lineas rectas y el texto b y n (negativo)
	############################################################################
	lower = np.array([32,31,35])  #-- Lower range --
	upper = np.array([32,31,35])  #-- Upper range --
	mask_bw_negative = cv.inRange(src, lower, upper)
	cv.imwrite('mask_bw_negative.png', mask_bw_negative)

	############################################################################
	# Quito artefactos de hasta una cierta superficie
	############################################################################
	min_size = 1000
	nb_components, output, stats, centroids = cv.connectedComponentsWithStats(mask_bw_negative, connectivity=8)
	sizes = stats[1:, -1]
	nb_components = nb_components - 1
	clean_mask = np.zeros((output.shape))
	for i in range(0, nb_components):
		if sizes[i] >= min_size:
			clean_mask[output == i + 1] = 255

	cv.imwrite('clean_mask.png', clean_mask)
	clean_mask = cv.imread('clean_mask.png')

	clean_mask_gray = cv.cvtColor(clean_mask,cv.COLOR_BGR2GRAY)
	cv.imwrite('clean_mask_gray.png', clean_mask_gray)

	############################################################################
	# Remuevo las líneas para recortar luego sin estas
	############################################################################
	cdstP = np.copy(src)
	cdstP = cv.bitwise_not(cdstP,cdstP,mask=clean_mask_gray)

	height, width, channels = cdstP.shape
	blank_image = np.zeros((height,width,3), np.uint8)

	in_res = 300
	minLineLength = 300*(300/in_res)
	maxLineGap = 300*(300/in_res)
	thres = int(150*(300/in_res))
	rho=1
	linesP = cv.HoughLinesP(clean_mask_gray,rho, np.pi/180,thres,minLineLength = minLineLength,maxLineGap = maxLineGap)
	if linesP is not None:

		ll = [e[0] for e in np.array(linesP).tolist()]
		ll = process_lines(ll, in_res)
		for l in [e[1] for e in enumerate(ll)]:
			cv.line(cdstP, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)
			cv.line(blank_image, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)

	mx_area = 2200*3000 # máxima area del rectangulo
	mx_area = 2200*3000 # máxima area del rectangulo

	cv.imwrite('blank_image.png', blank_image)
	cv.imwrite('final.png', cdstP)

	############################################################################
	# En bae a la mascara obtengo los rectanfulos de interes
	############################################################################
	gray = cv.cvtColor(blank_image, cv.COLOR_BGR2GRAY) # convert to grayscale
	retval, thresh_gray = cv.threshold(gray, thresh=1, maxval=255, \
                                   type=cv.THRESH_BINARY_INV)

	cv.imwrite('thresh_gray.png', thresh_gray)

	image, contours, hierarchy = cv.findContours(thresh_gray,cv.RETR_CCOMP , \
									cv.CHAIN_APPROX_SIMPLE )

	############################################################################
	# Recorto los rectangulos
	############################################################################
	mx_area = 2200*3000 # máxima area del rectangulo
	i = 1
	for cont in contours:
		x,y,w,h = cv.boundingRect(cont)
		area = w*h
		if area < mx_area:
			mx = x,y,w,h
			# pprint.pprint(mx)
			roi=src[y:y+h,x:x+w]
			cv.imwrite('{0}_crop_{1}.png'.format(filename,i), roi)
			i = i + 1

	# cv.namedWindow(filepath, cv.WINDOW_NORMAL)
	# cv.resizeWindow(filepath, 600,600)
	# cv.imshow(filepath, cdstP)
	# cv.waitKey()
	# cv.destroyAllWindows()


def process_lines(lista, in_res):

	top = int(240*in_res/300)
	left= int(80*in_res/300)
	# bottom = int(3260*in_res/300)
	# right = int(2300*in_res/300)

	############################################################################
	# Establezco el valor de y minímo para que caiga debajo de la recta 
	# horizontal del titulo de página
	############################################################################
	lista = [[left if l[0]-(left*2) < left else l[0], 
			  l[1] if l[1] > top else top,
		      left if l[2]-(left*2) < left else l[2], 
		      l[3] if l[3] > top else top]
			  for l in lista]

	############################################################################
	# Agregago el recuadro completo de la pagina
	############################################################################
	puntos=[(l[0],l[1]) for l in lista]
	puntos.extend([(l[2],l[3]) for l in lista])

	min_x = min([x for x,y in puntos]) - 50
	min_y = min([y for x,y in puntos])
	max_x = max([x for x,y in puntos]) + 50
	max_y = max([y for x,y in puntos])

	lista.append([min_x, min_y, max_x, min_y])
	lista.append([min_x, min_y, min_x, max_y])
	lista.append([min_x, max_y, max_x, max_y])
	lista.append([max_x, max_y, max_x, min_y])

	############################################################################
	# Simplifico las líneas
	############################################################################
	# level = 55
	# aprox = {0:{}, 1:{}}

	# for i in (0,1):
	# 	valor = list(sum(list(zip(*[(e[0+i], e[2+i]) for e in lista])), ()))
	# 	print(valor)
	# 	for e in valor:
	# 		if e not in aprox[i]:
	# 			aprox[i].update({e-x: e for x in range(-level, level + 1, 1)})


	# for i,e in enumerate(lista):
	# 	lista[i][0] = aprox[0][e[0]]
	# 	lista[i][1] = aprox[1][e[1]]
	# 	lista[i][2] = aprox[0][e[2]]
	# 	lista[i][3] = aprox[1][e[3]]


	############################################################################
	# Simplifico las líneas
	############################################################################
	level = 55
	aprox = {0:{}, 1:{}}

	i = 0
	valor = list(sum(list(zip(*[(e[0+i], e[2+i]) for e in lista])), ()))
	for e in valor:
		if e not in aprox[i]:
			aprox[i].update({e-x: e for x in range(-level, level + 1, 1)})


	for i,e in enumerate(lista):
		lista[i][0] = aprox[0][e[0]]
		lista[i][2] = aprox[0][e[2]]


	############################################################################
	# Ordeno y me quedo con las líneas no repetidas
	############################################################################
	lista.sort()
	lista = list(e for e,_ in itertools.groupby(lista))

	return(lista)

def remove_lines(lista, maxtop, maxbottom):

	lista = [l for l in lista if l[0] > maxtop and not (l[0] > maxbottom and l[2] > maxbottom)]


def add_box(lista, top, bottom, right, left):

	puntos=[(l[0],l[1]) for l in lista]
	puntos.extend([(l[2],l[3]) for l in lista])

	min_x = min([x for x,y in puntos]) - 50
	min_y = min([y for x,y in puntos])
	max_x = max([x for x,y in puntos]) + 50
	max_y = max([y for x,y in puntos])

	lista.append([min_x, min_y, max_x, min_y])
	lista.append([min_x, min_y, min_x, max_y])
	lista.append([min_x, max_y, max_x, max_y])
	lista.append([max_x, max_y, max_x, min_y])


def simplificar(mylista, level=5):

	aprox = {0:{}, 1:{}}

	for i in (0,1):
		valor = list(sum(list(zip(*[(e[0+i], e[2+i]) for e in mylista])), ()))
		for e in valor:
			if e not in aprox[i]:
				aprox[i].update({e-x: e for x in range(-level, level + 1, 1)})

	for i,e in enumerate(mylista):
		mylista[i][0] = aprox[0][e[0]]
		mylista[i][1] = aprox[1][e[1]]
		mylista[i][2] = aprox[0][e[2]]
		mylista[i][3] = aprox[1][e[3]]

def main(argv):

	file_pattern = argv[0] if len(argv) > 0 else "./boletines/img/*.png"
	for f in glob.glob(file_pattern):
		detect_lines(f)

	return 0

if __name__ == "__main__":
	main(sys.argv[1:])
