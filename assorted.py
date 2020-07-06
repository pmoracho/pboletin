from pprint import pprint
import opencv as cv
import numpy as np


def print_lineas(mylista):
    verticales = [l for l in mylista if l[0] == l[2]]
    horizontales = [l for l in mylista if l[1] == l[3]]

    print("Verticales ------------------------------")
    pprint(verticales)
    print("Horizontales ----------------------------")
    pprint(horizontales)
    print("-----------------------------------------")


def show_lines(img, lista):

    new = np.copy(img)

    for linea in [e[1] for e in enumerate(lista)]:
        cv.line(new, (linea[0], linea[1]), (linea[2], linea[3]), (0, 0, 255), 3, cv.LINE_AA)

    cv.namedWindow("window", cv.WND_PROP_FULLSCREEN)
    cv.setWindowProperty("window", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
    cv.imshow("window", new)
    cv.waitKey(0)
