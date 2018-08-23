

import numpy as np
import cv2

"""
cv2.imshow('hough',edges)
cv2.waitKey(0)
minLineLength=100
lines = cv2.HoughLinesP(image=edges,
                        rho=0.5,
                        theta=np.pi/300, 
                        threshold=100,
                        lines=np.array([]), 
                        minLineLength=minLineLength,
                        maxLineGap=1)

a,b,c = lines.shape
for i in range(a):
    cv2.line(gray, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (0, 0, 255), 3, cv2.LINE_AA)

cv2.imshow('hough',gray)
cv2.waitKey(0)

"""
    
# img = cv2.imread(('./tests/data/005.png'))
img = cv2.imread(('C:/Users/pmoracho/AppData/Local/Temp/tmpb43l3f8u/04.clean_mask_gray.png'))
clean_mask = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

"""
############################################################################
# Quito artefactos de hasta una cierta superficie
############################################################################
mask_bw_negative = cv2.inRange(img, (32,31,35), (32,31,35))
nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(mask_bw_negative, connectivity=8)
sizes = stats[1:, -1]
nb_components = nb_components - 1
clean_mask = np.zeros((output.shape[0], output.shape[1], 3), dtype = "uint8")

for i in range(0, nb_components):
  if sizes[i] >= 100:
    clean_mask[output == i + 1] = 255

clean_mask = cv2.cvtColor(clean_mask, cv2.COLOR_BGR2GRAY)

cv2.imshow('result', clean_mask)
cv2.waitKey(0)
"""
"""
edges = cv2.Canny(gray,50,150,apertureSize = 3)
kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (2, 2)) 
edges = cv2.dilate(edges, kernel, iterations=5)
cv2.imshow('result', edges)
cv2.waitKey(0)
"""
minLineLength=100
lines = cv2.HoughLinesP(image=clean_mask,
                        rho=0.02,
                        theta=np.pi/500,
                        threshold=80,
                        lines=np.array([]), 
                        minLineLength=minLineLength,
                        maxLineGap=1)

a,b,c = lines.shape
for i in range(a):
    cv2.line(img, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (0, 0, 255), 3, cv2.LINE_AA)


cv2.imshow('result', img)
cv2.waitKey(0)
cv2.destroyAllWindows()

"""

"""
    