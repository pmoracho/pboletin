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


def compare_images(outpath):

    import glob

    carpeta_recortes = os.path.join(outpath, 'jpg')
    for f in glob.glob( os.path.join(carpeta_recortes, "*.jpg")):
        filename = os.path.basename(f)
        acta, file_extension = os.path.splitext(filename)

        recorte = os.path.join(outpath, 'jpg', "{0}.jpg".format(acta))
        logo = os.path.join(outpath, 'logos', "{0}.jpg".format(acta))
        recorte = recorte if os.path.isfile(recorte) else text_img(outpath, "No existe recorte acta: {0}".format(acta))
        logo = logo if os.path.isfile(logo) else text_img(outpath, "No existe logo acta: {0}".format(acta))
        """
        imgs = {
            "Acta : {0} (recorte)".format(acta): cv2.imread(recorte),
            "Acta : {0} (logo)".format(acta): cv2.imread(logo)
        }
        """
        img1, img2 = cv2.imread(recorte), cv2.imread(logo)
        merged = merge_h_images(img1, img2)
        cv2.namedWindow(acta, cv2.WND_PROP_AUTOSIZE)
        cv2.imshow(acta, merged)
        """
        for k, img in imgs.items():
            cv2.namedWindow(k, cv2.WND_PROP_AUTOSIZE)
            cv2.imshow(k, img)
        """
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    """
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
    """


def merge_h_images(img1, img2):

    max_width = 0     # find the max width of all the images
    total_height = 0  # the total height of the images (vertical stacking)
    images = [img1, img2]
    for img in images:
        if img.shape[1] > max_width:
            max_width = img.shape[1]
        total_height += img.shape[0]

    merged = np.zeros((total_height, max_width, 3), dtype=np.uint8)
    merged.fill(255)

    current_y = 0  # keep track of where your current image was last placed in the y coordinate
    for image in images:
        merged[current_y:image.shape[0] + current_y, :image.shape[1], :] = image
        current_y += image.shape[0]

    return merged


def text_img(workpath, texto):
    size = cv2.getTextSize(texto, cv2.FONT_HERSHEY_COMPLEX, 2, 4)[0]
    im = np.ones((size[1], size[0]), np.uint8)*127
    cv2.putText(im, texto, (0, size[1]), cv2.FONT_HERSHEY_COMPLEX, 2, (0,), 4)
    cv2.putText(im, texto, (0, size[1]), cv2.FONT_HERSHEY_COMPLEX, 2, (255,), 2)

    img = os.path.join(workpath, "text_img.png")

    cv2.imwrite(img, im)

    return(img)


################################################################################
#  Cuerpo principal
################################################################################
if __name__ == "__main__":

    compare_images('out/10008')
