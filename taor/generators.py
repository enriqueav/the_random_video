import pprint
import numpy as np
from numpy.random import choice, randint

from taor.shapes import BaseShape, Rectangle, Circle, Ellipse
from taor.color_factory import ColorFactory


class GeneratorFactory(object):
    """
    GeneratorFactory class.
    The factory class needs to be instantiated, it does not have the factory
    method as Abstract
    """
    def __init__(self, size):
        self.size = size
        self.config = dict(
            s_generators=["l", "x", "s", "w"],
            # p_generators=[0.35, 0.15, 0.15, 0.35],  # custom probabilities for each
            # p_generators=[0, 0, 1, 0],  # use only one of them
            p_generators=None,  # same probabilities for all
            max_thickness=10
        )

    def get_random_coordinate(self):
        """
        get_random_coordinate

        Return a random value between size of the canvas +- size/6
        """
        delta = int(self.size / 6)
        return randint(-delta, self.size + delta)

    def get_size(self):
        """
        get_random_size

        Return a random value between 1 and the size of the canvas + size/6
        """
        return randint(1, self.size)

    def get_coordinates(self, quantity):
        """
        get_coordinates

        Get a list of random values. The size of the list will be quantity
        """
        return [self.get_random_coordinate() for _ in range(quantity)]

    def get_sizes(self, quantity):
        """
        get_sizes

        Get a list of random sizes (non negatives)
        The size of the list will be quantity
        """
        return [self.get_size() for _ in range(quantity)]

    def get_thickness(self):
        """
        get_thickness
        Get a get_thickness for the outline. OpenCV allows this
        """
        return randint(1, self.config['max_thickness'] + 1)

    def create_generator(self):
        """
        create_generator

        This is the factory method. Pick a Generator type at random, taking
        from self.config["s_generators"], with the probabilities
        given by self.config["p_generators"].
        """
        color_factory = ColorFactory()
        generator_type = choice(self.config["s_generators"], p=self.config["p_generators"])
        initial_color = color_factory.get_rgb_color()
        thickness = self.get_thickness()
        origin = self.get_coordinates(2)

        if generator_type == "l":
            generator = Lasso(origin, initial_color, thickness=thickness)
        elif generator_type == "x":
            generator = Explosion(origin, initial_color, thickness=thickness)
        elif generator_type == "s":
            generator = StainGrid(origin, initial_color, thickness=thickness)
        elif generator_type == "w":
            generator = Worm(origin, initial_color, thickness=thickness)
        else:
            print("GeneratorFactory.create_generator error, "
                  "generator_type %s not supported" % generator_type)
            exit(0)

        return generator


class Generator(BaseShape):
    def __init__(self, origin, color, outline=None, thickness=1):
        super().__init__(origin, color, outline=None, thickness=thickness)

        self.origin = origin
        self.paint_coordinates = origin

        # Use the color picked as outline instead of fill
        p_color_as_outline = [0.85, 0.15]
        if choice([False, True], p=p_color_as_outline):
            self.color = None
            self.outline = color

        self.s = {}
        self.s['s_shapes'] = ["rectangle", "circle", "ellipse"]
        self.s['p_shapes'] = [0.5, 0.5, 0]

        # COLOR CHANGE
        self.s['change_color'] = choice([False, True], p=[0.5, 0.5])
        self.s['change_color_unison'] = choice([False, True], p=[0.85, 0.15])
        self.s['p_change_color_every_step'] = [0.7, 0.3]
        # COLOR JUMP
        self.s['change_color_jump_every_step'] = choice([False, True], p=[0.65, 0.35])
        self.s['min_color_jump'] = randint(1, 11)
        self.s['max_color_jump'] = randint(self.s['min_color_jump']+1, 41)

        self.s['color_jump'] = randint(self.s['min_color_jump'], self.s['max_color_jump'])

        # ALPHA  # there is no alpha in OpenCV
        # self.s['change_alpha'] = choice([False, True], p=[1, 0])
        # self.s['p_change_alpha_every_step'] = [0.8, 0.2]
        # self.s['alpha_jump'] = randint(1, 41)

        # SIZE
        self.s['min_size'] = randint(30, 60)
        self.s['max_size'] = randint(self.s['min_size']+1, 160+1)
        self.s['size'] = randint(self.s['min_size'], self.s['max_size'])
        self.s['size_2'] = randint(self.s['min_size'], self.s['max_size'])
        self.s['change_size_every_step'] = choice([False, True], p=[0.65, 0.35])

        # SHAKINESS: each iteration can be slightly off the original x, y
        self.s['use_shakiness'] = choice([False, True], p=[0.8, 0.2])
        self.s['shakiness'] = randint(1, int(self.s['size']/2))

        self.s['lifespan'] = randint(24*3, 24*30)
        self.finished = False
        self.step = 0

    def __str__(self):
        return "Generator %s with origin = %r and config %s" % (
            self.__class__.__name__,
            self.origin,
            pprint.pformat(self.s)
        )

    def move_origin(self, new_x, new_y):
        self.origin[0] = new_x
        self.origin[1] = new_y

    def validate_cc(self, component):
        return min(max(component, 0), 255)

    def adjust_color(self, color):
        if not color:
            return

        nb, ng, nr = color
        if self.s['change_color']:
            jump = self.s['color_jump']
            # Change all the channels at unison or separated
            if self.s['change_color_unison']:
                delta = randint(-jump, jump+1)
                nb = self.validate_cc(nb + delta)
                nr = self.validate_cc(nr + delta)
                ng = self.validate_cc(ng + delta)
            else:
                if choice([False, True], p=self.s['p_change_color_every_step']):
                    nb = self.validate_cc(nb + randint(-jump, jump + 1))
                if choice([False, True], p=self.s['p_change_color_every_step']):
                    nr = self.validate_cc(nr + randint(-jump, jump + 1))
                if choice([False, True], p=self.s['p_change_color_every_step']):
                    ng = self.validate_cc(ng + randint(-jump, jump + 1))

        # if self.s['change_alpha']:
        #     if choice([False, True], p=self.s['p_change_alpha_every_step']):
        #         alpha = self.validate_cc(
        #             alpha + randint(-self.s['alpha_jump'], self.s['alpha_jump'])
        #         )
        # return nb, ng, nr, alpha  # OpenCV does not have alpha
        return nb, ng, nr

    def new_step(self):
        # SHAKINESS
        x, y = self.origin
        if self.s['use_shakiness']:
            x += randint(-self.s['shakiness'], self.s['shakiness']+1)
            y += randint(-self.s['shakiness'], self.s['shakiness']+1)
        self.paint_coordinates = [x, y]

        # CHANGE COLOR
        self.color = self.adjust_color(self.color)
        self.outline = self.adjust_color(self.outline)

        # CHANGE SIZE
        if self.s['change_size_every_step']:
            self.s['size'] = randint(self.s['min_size'], self.s['max_size'])
            self.s['size_2'] = randint(self.s['min_size'], self.s['max_size'])

        if self.s['shape'] == "circle":
            points = self.paint_coordinates
            if self.color:
                r = Circle(points, self.s['size'], self.color, self.outline, -1)
            else:
                r = Circle(points, self.s['size'], self.color, self.outline, self.thickness)
        if self.s['shape'] == "rectangle":
            sizes = (self.s['size'], self.s['size'])
            if self.color:
                r = Rectangle(
                    self.paint_coordinates, sizes, self.color, self.outline, -1
                )
            else:
                r = Rectangle(
                    self.paint_coordinates, sizes, self.color, self.outline, self.thickness
                )

        if self.s['shape'] == "ellipse":
            sizes = (self.s['size'], self.s['size_2'])
            if self.color:
                r = Ellipse(
                    self.paint_coordinates, sizes, self.color, self.outline, -1
                )
            else:
                r = Ellipse(
                    self.paint_coordinates, sizes, self.color, self.outline, self.thickness
                )
        # print(r)
        r.lifespan = self.s['lifespan']
        self.step += 1
        return r

    @classmethod
    def get_delta(cls, direction):
        deltas = [
            [-1, -1],
            [0, -1],
            [1, -1],
            [1, 0],
            [1, 1],
            [0, 1],
            [-1, 1],
            [-1, 0]
        ]
        return deltas[direction]


class LineGenerator(Generator):
    def __init__(self, origin, color, outline=None, thickness=1):
        super().__init__(origin, color, outline=outline, thickness=thickness)
        self.s['p_shapes'] = [0.4, 0.4, 0.2]
        self.s['shape'] = choice(self.s['s_shapes'], p=self.s['p_shapes'])
        self.s['max_space_jump'] = randint(1, self.s['size']+1)
        self.s['space_jump'] = randint(1, self.s['max_space_jump']+1)
        self.s['change_space_jump_every_step'] = choice([False, True], p=[0.7, 0.3])


class Worm(LineGenerator):
    def __init__(self, origin, color, outline=None, thickness=1):
        super().__init__(origin, color, outline=outline, thickness=thickness)
        # TODO: better document this
        craziness = int(np.sqrt(randint(1, 8**2)))
        p_no_change = 1 - (craziness/100)
        remaining = 1 - p_no_change
        p_1d = np.float(round(remaining*0.5, 3))
        p_2d = np.float(round(remaining*0.3, 3))
        p_3d = np.float(round(remaining*0.2, 3))
        p_no_change = 1 - p_1d - p_2d - p_3d
        self.s['p_change_direction'] = [p_no_change, p_1d, p_2d, p_3d]
        self.s['s_change_direction'] = [0, 1, 2, 3]

        # initial state
        self.direction = randint(0, 8)

    def generate(self):
        artifacts = []
        artifacts.append(self.new_step())

        delta = choice(self.s['s_change_direction'],
                       p=self.s['p_change_direction'])
        delta *= choice([-1, 1])
        self.direction = (self.direction + delta) % 8
        delta = Generator.get_delta(self.direction)

        if self.s['change_space_jump_every_step']:
            self.s['space_jump'] = randint(1, self.s['max_space_jump']+1)

        self.origin[0] += delta[0] * self.s['space_jump']
        self.origin[1] += delta[1] * self.s['space_jump']
        return artifacts


class Lasso(LineGenerator):
    def __init__(self, origin, color, outline=None, thickness=1):
        super().__init__(origin, color, outline=outline, thickness=thickness)
        craziness = int(np.sqrt(randint(2**2, 20**2)))
        p_no_change = 1 - (craziness/100)
        remaining = 1 - p_no_change
        p_1d = np.float(round(remaining*0.4, 3))
        p_2d = np.float(round(remaining*0.3, 3))
        p_3d = np.float(round(remaining*0.3, 3))
        p_no_change = 1 - p_1d - p_2d - p_3d
        self.s['p_change_direction'] = [p_no_change, p_1d, p_2d, p_3d]
        self.s['s_change_direction'] = [0, 1, 2, 3]
        self.s['max_grade'] = 3
        self.s['change_grade'] = randint(-self.s['max_grade'], self.s['max_grade']+1)

        # initial state
        self.s['direction'] = randint(0, 360)
        self.s['reset_every_frames'] = randint(96, 480)
        # pprint.pprint(self.s)

    def generate(self):
        artifacts = []
        artifacts.append(self.new_step())

        delta = [
            np.cos(np.radians(self.s['direction'])),
            np.sin(np.radians(self.s['direction'])),
        ]

        if self.s['change_space_jump_every_step']:
            self.s['space_jump'] = randint(1, self.s['max_space_jump']+1)

        delta_grade = choice(self.s['s_change_direction'],
                             p=self.s['p_change_direction'])
        delta_grade *= choice([-1, 1])
        self.s['change_grade'] = self.s['change_grade'] + delta_grade

        if self.step % self.s['reset_every_frames'] == 0:
            self.s['change_grade'] = 0

        self.s['direction'] = (self.s['direction'] + (self.s['change_grade']/4))

        self.origin[0] += delta[0] * self.s['space_jump']
        self.origin[1] += delta[1] * self.s['space_jump']
        return artifacts


class Explosion(Generator):
    """
    Explosion class. Experimental
    """
    def __init__(self, origin, color, outline=None, thickness=1):
        super().__init__(origin, color, outline=outline, thickness=1)
        self.s['quantity'] = randint(100, 5000)
        self.s['p_shapes'] = [0.3, 0.5, 0.2]
        self.s['shape'] = choice(self.s['s_shapes'], p=self.s['p_shapes'])
        # ANGLE
        self.s['min_angle_jump'] = randint(10, 21)
        self.s['max_angle_jump'] = randint(self.s['min_angle_jump']+1, 61)
        self.s['change_angle_jump_every_step'] = choice([False, True], p=[0.7, 0.3])
        self.s['angle_sign'] = choice([-1, 1])

        # DISTANCE FROM ORIGIN
        self.s['distance_jump'] = randint(1, 5)

        # initialized now, may be or may not be updated every step
        self.s['angle_jump'] = randint(self.s['min_angle_jump'], self.s['max_angle_jump']+1)
        self.s['direction'] = randint(0, 360)
        self.s['initial_distance'] = choice([0, randint(1, 100)])
        self.s['distance'] = self.s['initial_distance']
        self.s['reset_every_frames'] = randint(240, 480*2)

        self.s['initial_distance'] = 0
        self.s['distance'] = 0

        self.center = self.origin.copy()

    def reset(self):
        self.s['distance'] = self.s['initial_distance']
        self.center = self.origin.copy()

    def move_origin(self, new_x, new_y):
        super().move_origin(new_x, new_y)
        self.reset()

    def generate(self):
        artifacts = []
        artifact = self.new_step()
        artifacts.append(artifact)

        if self.s['change_angle_jump_every_step']:
            self.s['angle_jump'] = randint(self.s['min_angle_jump'], self.s['max_angle_jump']+1)

        self.s['direction'] += (self.s['angle_jump']*self.s['angle_sign'])
        delta = [
            np.cos(np.radians(self.s['direction'])),
            np.sin(np.radians(self.s['direction'])),
        ]

        self.s['distance'] += self.s['distance_jump']
        self.origin[0] = self.center[0] + (delta[0] * self.s['distance'])
        self.origin[1] = self.center[1] + (delta[1] * self.s['distance'])

        if self.step % self.s['reset_every_frames'] == 0:
            self.reset()

        return artifacts


class StainGrid(Generator):
    """
    StainGrid class. Experimental
    """
    def __init__(self, origin, color, outline=None, thickness=1):
        super().__init__(origin, color, outline=outline, thickness=thickness)
        self.s['quantity'] = randint(1000, 20000)
        self.s['p_shapes'] = [0.4, 0.5, 0.1]
        self.s['shape'] = choice(self.s['s_shapes'], p=self.s['p_shapes'])
        self.s['size'] = randint(20, 51)
        # choice between a random space or exactly the same size
        self.s['space_jump'] = choice(
            [randint(10, self.s['size']*2), self.s['size']],
            p=[0.7, 0.3]
        )
        self.s['change_size_every_step'] = False

    def generate(self):
        artifacts = []
        artifacts.append(self.new_step())
        direction = randint(0, 8)
        delta = Generator.get_delta(direction)
        self.origin[0] += delta[0] * self.s['space_jump']
        self.origin[1] += delta[1] * self.s['space_jump']
        return artifacts
