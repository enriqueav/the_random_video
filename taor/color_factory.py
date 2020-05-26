"""
color_factory module.
"""
from numpy.random import randint


class ColorFactory(object):
    def __init__(self):
        # don't need a config for now
        self.config = dict()

    def get_rgb_color(self):
        """
        get_color
        Get 3 values representing B, G, R
        """
        blue = randint(0, 256)
        green = randint(0, 256)
        red = randint(0, 256)
        return blue, green, red
