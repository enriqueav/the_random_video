import numpy as np
import cv2
from numpy.random import randint, choice
from taor.color_factory import ColorFactory


class PostEffectFactory(object):
    """
    PostEffectFactory class.
    The factory class needs to be instantiated, it does not have the factory
    method as Abstract
    """
    def __init__(self, fps, size):
        self.shape = size
        self.img_height, self.img_width = size
        self.config = dict(
            s_post_efect_type=[
                "mirr", "mibo", "gray", "b&w", "colt", "gaus", "brig", "cont", "boom"
            ],
            # p_post_effect_type=[0.5, 0, 0.5, 0, 0, 0, 0, 0, 0],
            p_post_effect_type=None,

            s_mirror_box=["h", "v"],
            p_mirror_box=[0.5, 0.5],

            # mirroring in half, negative means lowerX or rightY
            s_mirroring=[None, "h", "v", "-h", "-v"],
            p_mirroring1=[0, 0.25, 0.25, 0.25, 0.25],
            p_mirroring2=[0.90, 0.025, 0.025, 0.025, 0.025],

            s_gauss_filter_size=[9, 11, 13, 15, 21],
            p_gauss_filter_size=[0.1, 0.2,  0.3, 0.3, 0.1],

            min_diff_brightness=50,
            max_diff_brightness=100,

            s_contour_thickness=[3, 5, 7],
            p_contour_thickness=[0.4, 0.3, 0.3]
        )
        self.fps = fps
        # self.color_factory = ColorFactory()

    def create_post_effect(self):
        effect_type = choice(self.config["s_post_efect_type"],
                             p=self.config["p_post_effect_type"])

        if effect_type == "mirr":
            mirroring_axis1 = choice(self.config["s_mirroring"], p=self.config["p_mirroring1"])
            mirroring_axis2 = choice(self.config["s_mirroring"], p=self.config["p_mirroring2"])
            if mirroring_axis1 and mirroring_axis2 and \
                    mirroring_axis1.replace("-", "") == mirroring_axis2.replace("-", ""):
                mirroring_axis2 = None
            change = Mirror(self.fps, self.shape, mirroring_axis1, mirroring_axis2)
        elif effect_type == "mibo":
            mirror_box_axis = choice(self.config["s_mirror_box"], p=self.config["p_mirror_box"])
            height, width = self.shape
            x_initial = randint(0, width)
            y_initial = randint(0, height)
            x_final = randint(x_initial, width + 1)
            y_final = randint(y_initial, height + 1)
            box = (y_initial, x_initial, y_final, x_final)
            change = MirrorBox(self.fps, self.shape, mirror_box_axis, box)
        elif effect_type == "gray":
            change = GrayScale(self.fps, self.shape)
        elif effect_type == "b&w":
            change = BlackAndWhite(self.fps, self.shape)
        elif effect_type == "colt":
            color_factory = ColorFactory()
            color = color_factory.get_rgb_color()[:3]
            change = ColorThreshold(self.fps, self.shape, color)
        elif effect_type == "gaus":
            gauss_size = choice(self.config["s_gauss_filter_size"],
                                p=self.config["p_gauss_filter_size"])
            change = GaussianBlur(self.fps, self.shape, gauss_size)
        elif effect_type == "brig":
            diff = randint(self.config["min_diff_brightness"],
                           self.config["max_diff_brightness"])
            diff *= choice([-1, 1])
            change = Brightness(self.fps, self.shape, diff)
        elif effect_type == "cont":
            color_factory = ColorFactory()
            color = color_factory.get_rgb_color()[:3]
            thickness = choice(self.config["s_contour_thickness"],
                               p=self.config["p_contour_thickness"])
            change = Contour(self.fps, self.shape, color, thickness)
        elif effect_type == "boom":
            change = Boomerang(self.fps, self.shape)
        else:
            print("BG change type %r not supported yet" % effect_type)
            exit(1)
        return change


class PostEffect(object):

    def __init__(self, fps, img_shape):
        self.shape = img_shape
        self.img_height, self.img_width = img_shape
        self.fps = fps
        self.working = True
        self.finished = False

        min_frames = self.fps * 10
        max_frames = self.fps * 60
        self.frames = randint(min_frames, max_frames + 1)
        self.frame = 0

    def next_step(self, frame):
        if self.frame < self.frames:
            img = frame.copy()
            frame = self.process_effect(img)
            self.frame += 1
        else:
            self.working = False
            self.finished = True
        return frame

    def get_frames(self):
        return self.frames

    def process_effect(self):
        print("Not implemented %r" % self.__class__)
        return None

    def __repr__(self):
        return "PostEffect of type %s for %d seconds" \
               % (self.__class__.__name__, round(self.frames/self.fps))

    def is_working(self):
        return self.working

    def has_finished(self):
        return self.finished


class Mirror(PostEffect):
    """mirror effect

    Creates a mirrored version of an already finished image.

    Arguments:
        fps: Frames per seconds

        axis1 and axis2:
         "h" for horizontal
         "v" for vertical
         "-h" horizontal, mirror the lower part
         "-v" vertical, mirror the right part
         None, if no mirroring should be made

    Returns:
        image: Image
    """
    def __init__(self, fps, img_shape, axis_1, axis_2):
        super().__init__(fps, img_shape)
        self.axis_1 = axis_1
        self.axis_2 = axis_2

    def process_effect(self, frame):
        frame = self.process_axis(frame, self.axis_1)
        frame = self.process_axis(frame, self.axis_2)
        return frame

    def process_axis(self, image, axis):
        if not axis:
            return image

        height, width = self.shape
        if axis == "h":
            box = (0, 0, int(height/2), width)
            flip_method = 0
            paste_point = (int(height/2), 0, height, width)
        elif axis == "v":
            box = (0, 0, height, int(width/2))
            flip_method = 1
            paste_point = (0, int(width/2), height, width)
        elif axis == "-h":
            box = (int(height/2), 0, height, width)
            flip_method = 0
            paste_point = (0, 0, int(height/2), width)
        elif axis == "-v":
            box = (0, int(width/2), height, width)
            flip_method = 1
            paste_point = (0, 0, height, int(width/2))
        else:
            print("post_effects.mirror error, axis %s not supported" % axis)
            exit(0)

        flipped = cv2.flip(image[box[0]:box[2], box[1]:box[3]], flip_method)
        image[paste_point[0]:paste_point[2], paste_point[1]:paste_point[3]] = flipped
        return image


class MirrorBox(PostEffect):
    """mirror box effect

    Choose a random box and apply a mirror effect

    Arguments:
        image: The finished image
               finished means it already has the shapes and colors

        axis:
         "h" for horizontal
         "v" for vertical

    Returns:
        image: Image
    """
    def __init__(self, fps, img_shape, axis, box):
        super().__init__(fps, img_shape)
        self.axis = axis
        self.box = box

    def process_effect(self, image):
        box = self.box

        if self.axis == "h":
            flip_method = 0
        elif self.axis == "v":
            flip_method = 1
        else:
            print("post_effects.mirror_box error, axis %s not supported" % self.axis)
            exit(0)

        flipped = cv2.flip(image[box[0]:box[2], box[1]:box[3]], flip_method)
        image[box[0]:box[2], box[1]:box[3]] = flipped
        return image


class GrayScale(PostEffect):
    """
    Convert to grayscale
    """
    def process_effect(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)


class BlackAndWhite(PostEffect):
    """
    Convert to binary
    """
    def process_effect(self, image):
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(img_gray, 255,
                                       cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)


class ColorThreshold(PostEffect):
    """
    Convert to binary and paint with a color
    """
    def __init__(self, fps, img_shape, color):
        super().__init__(fps, img_shape)
        self.color = color

    def process_effect(self, image):
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(img_gray, 255,
                                       cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
        # ones = np.count_nonzero(thresh)
        # zeros = thresh.size - ones
        back2color = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        back2color[np.where((back2color == [0, 0, 0]).all(axis=2))] = self.color
        return back2color


class GaussianBlur(PostEffect):
    """
    Gaussian Blur to ridiculous sizes
    """
    def __init__(self, fps, img_shape, gauss_size):
        super().__init__(fps, img_shape)
        self.gauss_size = gauss_size

    def __repr__(self):
        return "GaussianBlur for %d seconds and size %d" \
               % (round(self.frames/self.fps), self.gauss_size)

    def process_effect(self, image):
        return cv2.GaussianBlur(image, (self.gauss_size, self.gauss_size), 0)


class Brightness(PostEffect):
    """
    Brightness change
    """
    def __init__(self, fps, img_shape, diff):
        super().__init__(fps, img_shape)
        self.diff = diff
        if self.diff > 0:
            self.add = 1
        else:
            self.add = -1
        self.current = 0

    def __repr__(self):
        return "Brightness for %d seconds and diff %d" \
               % (round(self.frames/self.fps), self.diff)

    def process_effect(self, image):
        pseudo_image = np.int32(image) + self.current
        pseudo_image[pseudo_image > 255] = 255
        pseudo_image[pseudo_image < 0] = 0

        if self.frame <= abs(self.diff):
            self.current += self.add
        elif self.frames - self.frame <= abs(self.diff):
            self.current -= self.add
        return np.uint8(pseudo_image)


class Contour(PostEffect):
    """
    Find and paint contours change
    """
    def __init__(self, fps, img_shape, color, thickness):
        super().__init__(fps, img_shape)
        self.color = color
        self.thickness = thickness

    def __repr__(self):
        return "Contour for %d seconds with thickness %d" \
               % (round(self.frames/self.fps), self.thickness)

    def process_effect(self, image):
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        img_gray = cv2.bilateralFilter(img_gray, 9, 75, 75)
        thresh = cv2.adaptiveThreshold(
            img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 2
        )
        kernel = np.ones((5, 5), np.uint8)
        # thresh = cv2.dilate(thresh, kernel, iterations=1)
        thresh = 255 - thresh  # superhack
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        im2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        # print(hierarchy)
        cv2.drawContours(image, contours, -1, self.color, self.thickness)
        # return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        return image


class Boomerang(PostEffect):
    """
    Boomerang Effect
    """
    def __init__(self, fps, img_shape):
        super().__init__(fps, img_shape)
        self.buffer = []
        self.effect_length = randint(self.fps, self.fps*2)
        self.times = self.frames // (self.effect_length*2)
        self.increment = 1
        self.buffer_index = self.effect_length - 1
        self.reached_limit = 0

    def __repr__(self):
        return "Boomerang for %d seconds with effect length %d for %d times" \
               % (round(self.frames/self.fps), self.effect_length, self.times)

    def process_effect(self, image):
        if len(self.buffer) < self.effect_length:
            self.buffer.append(image.copy())
        else:
            if self.reached_limit < 3:
                ret_val = self.buffer[self.buffer_index]

                if self.buffer_index == 0:
                    self.increment = 1
                    self.reached_limit += 1
                if self.buffer_index == self.effect_length - 1:
                    self.increment = -1
                    self.reached_limit += 1
                self.buffer_index += self.increment
                return ret_val
            else:
                self.buffer = []
                self.reached_limit = 0
                self.buffer_index = self.effect_length - 1
        return image
