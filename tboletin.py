"""
@file hough_lines.py
@brief This program demonstrates line finding with the Hough transform
"""
import sys
import math
import cv2 as cv
import numpy as np
import glob
from operator import itemgetter
import pprint
import itertools

def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	v = np.median(image)
	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edged = cv.Canny(image, lower, upper)
	# return the edged image
	return edged
 

def detect_lines(filepath):

    src = cv.imread(filepath)
    if src is None:
        print ('Error opening {0}!'.format(filepath))
        return -1

    ##################################################################################################
    # Me quedo solo con el color de las lineas rectas y el texto b y n (negativo)
    ##################################################################################################
    lower = np.array([32,31,35])  #-- Lower range --
    upper = np.array([32,31,35])  #-- Upper range --
    mask_bw_negative = cv.inRange(src, lower, upper)
    cv.imwrite('mask_bw_negative.png', mask_bw_negative)

    ##################################################################################################
    # Quito artefactos de hasta una cierta superficie
    ##################################################################################################
    # minimum size of particles we want to keep (number of pixels)
    #here, it's a fixed value, but you can set it as you want, eg the mean of the sizes or whatever
    min_size = 1000  
    #find all your connected components (white blobs in your image)
    nb_components, output, stats, centroids = cv.connectedComponentsWithStats(mask_bw_negative, connectivity=8)
    #connectedComponentswithStats yields every seperated component with information on each of them, such as size
    #the following part is just taking out the background which is also considered a component, but most of the time we don't want that.
    sizes = stats[1:, -1]; nb_components = nb_components - 1
    #your answer image
    clean_mask = np.zeros((output.shape))
    #for every component in the image, you keep it only if it's above min_size
    for i in range(0, nb_components):
      if sizes[i] >= min_size:
          clean_mask[output == i + 1] = 255
          
    cv.imwrite('clean_mask.png', clean_mask)
    clean_mask = cv.imread('clean_mask.png')
    
    clean_mask_gray = cv.cvtColor(clean_mask,cv.COLOR_BGR2GRAY)
    cv.imwrite('clean_mask_gray.png', clean_mask_gray)



    """
    cdstP = np.copy(src)
    binary = cv.bitwise_not(clean_mask_gray)
    (_,contours,_) = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)

    for contour in contours:
        rect = cv.boundingRect(contour)
        cv.rectangle(cdstP, (rect[0],rect[1]), (rect[2]+rect[0],rect[3]+rect[1]), (0,255,0), 2)
        
    cv.imwrite('contornos.png', cdstP)
    """
    
    cdstP = np.copy(src)
    in_res = 300
    minLineLength = 300
    maxLineGap = 300
    rho=1
    linesP = cv.HoughLinesP(clean_mask_gray,
                             rho,
                             np.pi/180,150, 
                             minLineLength = minLineLength,
                             maxLineGap = maxLineGap)
    

    
    if linesP is not None:
        top = 120*in_res/150
        bottom = 1634*in_res/150
        lineas = [line for line in linesP if line[0][1] > top and not (line[0][1] > bottom and line[0][3] > bottom)]
        
        for i,l in enumerate(lineas):
          if l[0][1] < top:
              lineas[i][0][1] = top
          if l[0][3] < top:
              lineas[i][0][3] = top
       
        ll = [e[0] for e in np.array(lineas).tolist()]
        pprint.pprint(ll)
        ll = simplificar(ll)
      
        # Recuadro principal
        puntos=[(l[0],l[1])  for l in ll]
        puntos.extend([(l[2],l[3])  for l in ll])
        
        min_x = min([x for x,y in puntos])
        min_y = min([y for x,y in puntos])
        max_x = max([x for x,y in puntos])
        max_y = max([y for x,y in puntos])
        
        ll.append([min_x, min_y, max_x, min_y])
        ll.append([min_x, min_y, min_x, max_y])
        ll.append([min_x, max_y, max_x, max_y])
        ll.append([max_x, max_y, max_x, min_y])

        ll.sort()
        ll = list(e for e,_ in itertools.groupby(ll))

        print(filepath)
        pprint.pprint(ll)
        print("------------------------------------")

        for l in [e[1] for e in enumerate(ll)]:
            cv.line(cdstP, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)

        print(len(ll))
        
    cv.imwrite('final.png', cdstP)

    cv.namedWindow(filepath, cv.WINDOW_NORMAL) 
    cv.resizeWindow(filepath, 600,600)
    cv.imshow(filepath, cdstP)
    cv.waitKey()
    cv.destroyAllWindows()

def simplificar(mylista):

    aprox = {0:{}, 1:{}}
    
    for i in (0,1):
      valor = list(sum(list(zip(*[(e[0+i], e[2+i]) for e in mylista])), ()))
      for e in valor:
        if e not in aprox[i]:
          aprox[i].update({e-5:e,e-4:e,e-3:e,e-2:e,e-1:e,e-0:e,e+1:e,e+2:e,e+3:e,e+4:e,e+5:e})

    for i,e in enumerate(mylista):
      
      mylista[i][0] = aprox[0][e[0]]
      mylista[i][1] = aprox[1][e[1]]
      mylista[i][2] = aprox[0][e[2]]
      mylista[i][3] = aprox[1][e[3]]

    return(mylista)

def main(argv):
    
    file_pattern = argv[0] if len(argv) > 0 else "./img/*.png"
    
    for f in glob.glob(file_pattern):
        detect_lines(f)
    return 0
    
if __name__ == "__main__":
    main(sys.argv[1:])