"""
Shapes module.
Contains the abstract class Shape and all its children
"""
from abc import ABCMeta
import cv2
import numpy as np


class BaseShape(object):
    """
    BaseShape class.
    Abstract class to represent a Shape to be drawn in an image.
        It has a (initial) coordinate, color and outline
    """
    __metaclass__ = ABCMeta

    def __init__(self, origin, color, outline=None, thickness=1):
        self.origin = np.array(origin, dtype=np.int16)
        self.color = color
        self.outline = outline
        self.thickness = thickness
        self.lifespan = 0
        self.age = 0
        self.dead = False
        self.painted = False

    def get_origin(self):
        return self.origin

    def move_yx(self, move_x, move_y):
        self.origin[0] += move_x or 0
        self.origin[1] += move_y or 0


class Rectangle(BaseShape):
    """
    Rectangle class.
    Concrete implementation of Shape, maps almost directly to
        -cv2.rectangle
    """
    def __init__(self, origin, sizes, color, outline=None, thickness=1):
        super().__init__(origin, color, outline=outline, thickness=thickness)
        self.height, self.width = sizes

    def __str__(self):
        return "Rectangle. O:%r, H:%d, W:%d, C:%r, O:%r, T:%r" % \
               (self.origin, self.height, self.width, self.color, self.outline, self.thickness)

    def draw(self, img):
        origin = tuple(self.origin)
        end = tuple([self.origin[0]+self.width, self.origin[1]+self.height])
        if self.color:
            cv2.rectangle(
                img, origin, end, self.color, -1
            )
        if self.outline:
            cv2.rectangle(
                img, origin, end, self.outline, self.thickness, cv2.LINE_AA
            )

    def will_paint(self, canvas_size):
        canvas_w, canvas_h = canvas_size

        if (self.origin[0] > canvas_w or self.origin[0]+self.width < 0
                or self.origin[1] > canvas_h or self.origin[1]+self.height < 0):
            return False
        return True


class Ellipse(BaseShape):
    """
    Ellipse class.
    Concrete implementation of Shape, maps to
        -cv2.ellipse
    """
    def __init__(self, origin, sizes, color, outline=None, thickness=1):
        super().__init__(origin, color, outline=outline, thickness=thickness)
        self.axes = int(sizes[0]/2), int(sizes[1]/2)

    def __str__(self):
        return "Ellipse. O:%r, Axes:%r, C:%r, O:%r, T:%r" % \
               (self.origin, self.axes, self.color, self.outline, self.thickness)

    def draw(self, img):
        coord = self.origin
        if self.color:
            cv2.ellipse(img, tuple(coord[0:2]), self.axes,
                        0, 0, 360, self.color, -1, cv2.LINE_AA)
        if self.outline:
            cv2.ellipse(img, tuple(coord[0:2]), self.axes,
                        0, 0, 360, self.outline, self.thickness, cv2.LINE_AA)

    def will_paint(self, canvas_size):
        canvas_w, canvas_h = canvas_size
        axis_x, axis_y = self.axes

        if (self.origin[0]-axis_x > canvas_w or self.origin[0]+axis_x < 0
                or self.origin[1]-axis_y > canvas_h or self.origin[1]+axis_y < 0):
            return False
        return True


class Circle(BaseShape):
    """
    Circle class.
    Concrete implementation of Shape, to
        -cv2.circle
    But with some modifications
    """
    def __init__(self, origin, size, color, outline=None, thickness=1):
        super().__init__(origin, color, outline=outline, thickness=thickness)
        self.radius = round(size/2)

    def __str__(self):
        return "Circle. O:%r, R:%r, C:%r, O:%r, T:%r" % \
               (self.origin, self.radius, self.color, self.outline, self.thickness)

    def draw(self, img):
        coord = self.origin
        if self.color:
            cv2.circle(
                img, tuple(coord[0:2]), self.radius, self.color, -1, cv2.LINE_AA
            )
        if self.outline:
            cv2.circle(
                img, tuple(coord[0:2]), self.radius, self.outline, self.thickness, cv2.LINE_AA
            )

    def will_paint(self, canvas_size):
        canvas_w, canvas_h = canvas_size

        if (self.origin[0] + self.radius < 0
                or self.origin[0] - self.radius > canvas_w
                or self.origin[1] + self.radius < 0
                or self.origin[1] - self.radius > canvas_h):
            return False
        return True


class Polygon(BaseShape):
    """
    Polygon class.
    Concrete implementation of Shape, maps almost directly to
        -cv2.fillPoly

    The number of points received (coordinates) is variable, but it
    should be an even number >= 6 (three points, X and Y per each point)
    """
    def __init__(self, origin, additional, color, outline=None, thickness=1):
        self.coordinates = origin + additional
        super().__init__(origin, color, outline=outline, thickness=thickness)

    def __str__(self):
        return "Polygon. Points:%r, C:%r, O:%r, T:%r" % \
               (self.coordinates, self.color, self.outline, self.thickness)

    def draw(self, img):
        points = np.array(
            [[tuple(self.coordinates[i:i + 2]) for i in range(0, len(self.coordinates), 2)]]
        )
        cv2.fillPoly(img, points, self.color, cv2.LINE_AA)

    def get_coordinates(self):
        return self.coordinates

    def set_coordinates(self, new_points):
        if len(self.coordinates) != len(new_points):
            print("ERROR at polygon.set_coordinates, size does not match")
            print("%d vs %d" % (len(self.coordinates), len(new_points)))
            exit(1)
        self.coordinates = new_points
