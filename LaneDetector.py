import cv2
import numpy as np


class LaneIsolator(object):
    """ Base class that implements everything needed in order to properly
        isolate lane lines
    """

    def __init__(self, lane_camera=None):
        self.camera = lane_camera
        self.L_THRESHOLD = (120, 255)  # L in LUV color space
        self.S_THRESHOLD = (105, 255)  # S in HLS color space
        self.B_THRESHOLD = (180, 210)  # B in Lab color space
        self.MAG_THRESHOLD = (30, 235)  # Gradient magnitude
        self.DIR_THRESHOLD = (0, np.pi / 2)  # Gradient direction

    def isolate_lines(self, img):
        """ Isolates lane lines from the image using an ensemble of color and
            edge selection
            :param img: Input BGR image from the camera
            :return: A bitmap where 1s are the selected areas
        """
        equalized = self.eq_histogram(img)
        color_select = self.color_threshold(equalized)
        grad_select = self.gradient_threshold(equalized)
        selection = np.zeros_like(color_select)
        selection[(color_select == 1) | (grad_select == 1)] = 1
        return selection

    def _within_threshold(self, array, threshold=(0, 255)):
        """ Private method which takes an array and fills with ones the areas
            that were within the thresholded values
            :param array: An array to apply thresholding over
            :param threshold: A tuple containing the lower and upper bounds of
                              the threshold
            :return: A bitmap where 1s are the selected areas
        """
        min_val = threshold[0]
        max_val = threshold[1]
        thresholded = np.zeros_like(array)
        thresholded[(array >= min_val) & (array <= max_val)] = 1
        return thresholded

    def eq_histogram(self, img):
        """ Equalizes the histogram of the input image for better detection
        :param img: Input 3 channel image from the camera
        :return: An equalized 3 channel image
        """
        img[:, :, 0] = cv2.equalizeHist(img[:, :, 0])
        img[:, :, 1] = cv2.equalizeHist(img[:, :, 1])
        img[:, :, 2] = cv2.equalizeHist(img[:, :, 2])
        return img

    def color_threshold(self, img):
        """ Applies color selection over the image to attempt to isolate the lines
        :param img: Input BGR image from the camera
        :return: A bitmap where 1s are the selected areas
        """
        l_chan = cv2.cvtColor(img, cv2.COLOR_BGR2LUV)[:, :, 0]
        s_chan = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)[:, :, 2]
        b_chan = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)[:, :, 2]

        l_thresh = self._within_threshold(l_chan, self.L_THRESHOLD)
        s_thresh = self._within_threshold(s_chan, self.S_THRESHOLD)
        b_thresh = self._within_threshold(b_chan, self.B_THRESHOLD)

        selection = np.zeros_like(l_chan)
        # Color is sensitive, that's why it's an OR operator
        selection[(l_thresh == 1) & (s_thresh == 1) | (b_thresh == 1)] = 1

        return selection

    def gradient_threshold(self, img):
        """ Attempts to isolate the lane lines using edge gradients
        :param img: Input BGR image from the camera
        :return: A bitmap where 1s are the selected areas
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        magnitude = self._gradient_mag(gray)
        direction = self._gradient_dir(gray)

        mag_thresh = self._within_threshold(magnitude, self.MAG_THRESHOLD)
        dir_thresh = self._within_threshold(direction, self.DIR_THRESHOLD)

        selection = np.zeros_like(magnitude)
        selection[(mag_thresh == 1) & (dir_thresh == 1)] = 1

        return selection

    def _gradients(self, gray, kernel=3):
        """ Computes the edge gradients using the Sobel operator
        :param gray: Grayscaled input image
        :param kernel: Kernel size to use for Sobel
        :return: (x, y) tuple of x and y edge gradient magnitude
        """
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=kernel)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=kernel)
        return (grad_x, grad_y)

    def _gradient_mag(self, gray):
        """ Computes the magnitude map of the edge gradients
        :param gray: Grayscaled input image
        :return: Gradient magnitude matrix
        """
        grad_x, grad_y = self._gradients(gray)
        # Pythagoras
        magnitude = np.sqrt(np.square(grad_x) + np.square(grad_y))
        return magnitude

    def _gradient_dir(self, gray):
        """ Computes the direction map of the edge gradients
        :param gray: Grayscaled input image
        :return: Gradient direction matrix
        """
        grad_x, grad_y = self._gradients(gray)

        grad_x = np.absolute(grad_x)
        grad_y = np.absolute(grad_y)

        direction = np.arctan2(grad_y, grad_x)
        return direction
