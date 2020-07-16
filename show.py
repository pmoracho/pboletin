import cv2 as cv2
import numpy as np
import os


def show_results(workpath, outpath, lista_actas):

    img = cv2.imread(os.path.join(workpath, '06.original_con_lineas.png'))

    wname = "Original c/mascara"
    cv2.namedWindow(wname, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(wname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow(wname, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    for acta in lista_actas:
        recorte = os.path.join(outpath, 'jpg', "{0}.jpg".format(acta))
        logo = os.path.join(outpath, 'logos', "{0}.jpg".format(acta))

        recorte = recorte if os.path.isfile(recorte) else text_img(workpath, "No existe recorte acta: {0}".format(acta))
        logo = logo if os.path.isfile(logo) else text_img(workpath, "No existe logo acta: {0}".format(acta))

        imgs = {
            "Acta : {0} (recorte)".format(acta): cv2.imread(recorte),
            "Acta : {0} (logo)".format(acta): cv2.imread(logo)
        }

        for k, img in imgs.items():
            cv2.namedWindow(k, cv2.WND_PROP_AUTOSIZE)
            cv2.imshow(k, img)

        cv2.waitKey(0)
        cv2.destroyAllWindows()


def text_img(workpath, texto):
    size = cv2.getTextSize(texto, cv2.FONT_HERSHEY_COMPLEX, 2, 4)[0]
    im = np.ones((size[1], size[0]), np.uint8)*127
    cv2.putText(im, texto, (0, size[1]), cv2.FONT_HERSHEY_COMPLEX, 2, (0,), 4)
    cv2.putText(im, texto, (0, size[1]), cv2.FONT_HERSHEY_COMPLEX, 2, (255,), 2)

    img = os.path.join(workpath, "text_img.png")

    cv2.imwrite(img, im)

    return(img)
