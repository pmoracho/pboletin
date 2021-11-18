import cv2 as cv
import numpy as np

from pboletin import process_lines

def show_img(wname, img):
    cv.namedWindow(wname, cv.WND_PROP_FULLSCREEN)
    cv.setWindowProperty(wname, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
    cv.imshow(wname, img)
    cv.waitKey(0)
    cv.destroyAllWindows()

def detect_horizontal_lines(filepath, show=False):
    src = cv.imread(filepath)

    # if show:
    #     show_img("Original", src)


    mask_bw_negative = cv.inRange(src, np.array([0, 0, 0]), np.array([123, 123, 123]))
    # if show:
    #     show_img("Solo colores importantes", mask_bw_negative)
    """

    ############################################################################
    # Quito artefactos de hasta una cierta superficie
    ############################################################################
    nb_components, output, stats, centroids = cv.connectedComponentsWithStats(mask_bw_negative, connectivity=8)
    sizes = stats[1:, -1]
    nb_components = nb_components - 1
    clean_mask = np.zeros((output.shape[0], output.shape[1], 3), dtype="uint8")

    for i in range(0, nb_components):
        if sizes[i] >= 5:
            clean_mask[output == i + 1] = 255

    if show:
        show_img("Limpieza", clean_mask)
    ############################################################################
    # Engroso la máscara para no perder lineas rectas
    ############################################################################
    clean_mask_gray = cv.Canny(mask_bw_negative, 50, 150, apertureSize=3)
    kernel = cv.getStructuringElement(cv.MORPH_CROSS, (2, 2))
    clean_mask_gray = cv.dilate(clean_mask_gray, kernel, iterations=1)
    if show:
        show_img("Dilate", clean_mask_gray)
    pass
    """

    ############################################################################
    # Detección de líneas rectas y generación de máscara de recorte
    ############################################################################
    h_line_gap = 60
    v_line_gap = 60
    line_max_gap = 100
    line_thres = 1
    line_rho = 1
    theta = 300
    compensation = 0.5
    line_min_length = 2350
    resolution = 150

    height, width, channels = src.shape
    crop_mask = np.zeros((height, width, 3), np.uint8)
    minLineLength = int(line_min_length*compensation)
    maxLineGap = int(line_max_gap*compensation)
    theta = int(theta)
    thres = int(line_thres*compensation)
    rho = line_rho

    linesP = None
    linesP = cv.HoughLinesP(mask_bw_negative, rho, np.pi/theta, thres, minLineLength=minLineLength, maxLineGap=maxLineGap)


    if linesP is not None:

        llorig = [e[0] for e in np.array(linesP).tolist()]
        # for linea in [e[1] for e in enumerate(llorig)]:
        #     cv.line(original_original_con_lineas, (linea[0], linea[1]), (linea[2], linea[3]), (0, 0, 255), 3, cv.LINE_AA)
        # if show:
        #     show_img("Rectas", original_original_con_lineas)

        original_con_lineas = np.copy(src)
        ll = process_lines(src, llorig, resolution, True, h_line_gap, v_line_gap, compensation)
        for linea in [e[1] for e in enumerate(ll)]:
            cv.line(original_con_lineas, (linea[0], linea[1]), (linea[2], linea[3]), (0, 0, 255), 3, cv.LINE_AA)
        if show:
            show_img("Solo colores importantes", original_con_lineas)



if __name__ == "__main__":


    file = '/tmp/tmpy5ckehsc/pagina-10.png'
    detect_horizontal_lines(file, show=True)