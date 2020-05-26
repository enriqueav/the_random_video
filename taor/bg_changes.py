import numpy as np
from numpy.random import choice, randint

from taor.shapes import Polygon
from taor.color_factory import ColorFactory


class BackgroundFactory(object):
    """
    BackgroundFactory class.
    The factory class needs to be instantiated because the method
    create_bg_change is not abstract
    """
    def __init__(self, fps, size):
        self.img_height, self.img_width = size
        self.config = dict(
            s_background_change_type=[
                "rand", "inst", "conv", "grid", "cour", "poly", "nois"
            ],
            # p_background_change_type=[1, 0, 0, 0, 0, 0, 0],
            p_background_change_type=None,
        )
        self.fps = fps
        self.color_factory = ColorFactory()

    def create_bg_change(self, current_color=None):
        bg_change = choice(self.config["s_background_change_type"],
                           p=self.config["p_background_change_type"])

        target_color = self.color_factory.get_rgb_color()
        shape = (self.img_height, self.img_width)

        if bg_change == "inst":
            change = InstantChange(self.fps,
                                   shape,
                                   target_color)
        elif bg_change == "rand":
            change = RandomPixelChange(self.fps,
                                       shape,
                                       target_color)
        elif bg_change == "conv":
            change = ConvertChange(self.fps,
                                   shape,
                                   target_color,
                                   current_color=current_color)
        elif bg_change == "grid":
            change = GridChange(self.fps,
                                shape,
                                target_color)
        elif bg_change == "cour":
            change = CurtainChange(self.fps,
                                   shape,
                                   target_color)
        elif bg_change == "poly":
            change = PolygonChange(self.fps,
                                   shape,
                                   target_color,
                                   current_color=current_color)
        elif bg_change == "nois":
            change = RandomNoiseChange(self.fps,
                                       shape,
                                       target_color)
        else:
            print("BG change type %r not supported yet" % bg_change)
            exit(1)
        return change


class BackgroundChange(object):
    def __init__(self, fps, img_shape, target_color, current_color=None):
        self.img_height, self.img_width = img_shape
        self.fps = fps
        self.working = True
        self.target_color = target_color
        self.current_color = current_color
        self.finished = False
        self.frame = 0

    def __repr__(self):
        return "BackgroundChange of type %s. Target color: %r" \
               % (self.__class__.__name__, self.target_color)

    def is_working(self):
        return self.working

    def has_finished(self):
        return self.finished

    def get_final_color(self):
        return self.target_color


class SliceChange(BackgroundChange):
    """
    Abstract Class.
    Background change that changes a slice of the frames coordinates
    each frame.
        frame[slice_y, slice_x, :] = self.target_color

    Each implementation is responsible to create the slice depending on the
    type of change. For instance:
        - Random pixels
        - Divide the frame into a grid
        - etc

    The property self.points_per_frame rules how many of this slices should be changed
    each frame. For instance, if the slices are individual coordinates of pixels, we want
    to change several each frame, other wise it would take too long to convert all the pixels.
    """
    def __init__(self, fps, img_shape, target_color, current_color=None):
        super().__init__(fps, img_shape, target_color, current_color=current_color)
        self.points_per_frame = 1

    def next_step(self, frame):
        if len(self.coordinates) > 0:
            for _ in range(self.points_per_frame):
                if len(self.coordinates) > 0:
                    sy, sx = self.coordinates[0]
                    frame[sy, sx, :] = self.target_color[:3]
                    self.coordinates = self.coordinates[1:]
                else:
                    self.working = False
                    self.finished = True
        else:
            self.working = False
            self.finished = True
        return frame


class InstantChange(SliceChange):
    """
    InstantChange is the simples of changes. It extends SliceChange, but this
    slice is simply the whole frame. Changes from current color to target
    color in a single step.
    """
    def __init__(self, fps, img_shape, target_color):
        super().__init__(fps, img_shape, target_color)
        self.coordinates = [[slice(0, self.img_height+1),
                             slice(0, self.img_width+1)]]


class RandomPixelChange(SliceChange):
    """
    RandomPixelChange creates an array of all the possible pixel coordinates
    and shuffles them. It also picks randomly how many of these shuffled coordinates
    should be changed to target_color each frame.
    """
    def __init__(self, fps, img_shape, target_color):
        super().__init__(fps, img_shape, target_color)
        max_ppf = (self.img_width * self.img_height) / (self.fps * 2)
        min_ppf = (self.img_width * self.img_height) / (self.fps * 5)
        self.points_per_frame = randint(min_ppf, max_ppf+1)

        coordinates = []
        for w in range(self.img_width):
            for h in range(self.img_height):
                coordinates.append([slice(h, h+1), slice(w, w+1)])
        self.coordinates = np.array(coordinates)
        np.random.shuffle(self.coordinates)


class GridChange(SliceChange):
    """
    Also based on SliceChange, it creates the slices to divide the frame in
    a grid of [1 to 8] by [1 to 8]. This will create a total number of slices
    between 1 and 64. The resultant slices are then shuffled.
    """
    def __init__(self, fps, img_shape, target_color):
        super().__init__(fps, img_shape, target_color)
        div_x = randint(1, 9)
        div_y = randint(1, 9)
        jump_y = round(self.img_height/div_y)
        jump_x = round(self.img_width/div_x)

        coordinates = []
        for row in range(div_y):
            for col in range(div_x):
                y_initial = row*jump_y
                y_final = (row+1)*jump_y
                x_initial = col*jump_x
                x_final = (col+1)*jump_x

                # force-fix rounding problems
                if row == div_y-1:
                    y_final = self.img_height
                if col == div_x-1:
                    x_final = self.img_width

                coordinates.append([slice(int(y_initial), int(y_final+1)),
                                    slice(int(x_initial), int(x_final+1))])
        self.coordinates = np.array(coordinates)
        np.random.shuffle(self.coordinates)


class CurtainChange(SliceChange):
    """
    Creates a curtain effect from one side to the other, either vertically
    or horizontally.
    Since it would be too long to do it a single step per frame, it also
    chooses randomly a higher value of self.lines_per_frame
    """
    def __init__(self, fps, img_shape, target_color):
        super().__init__(fps, img_shape, target_color)

        # Up-Down, Down-Up, Left-Right, Right-Left
        s_directions = ["ud", "du", "lr", "rl"]
        direction = choice(s_directions)
        if direction in ["ud", "du"]:
            lines = self.img_height
        else:
            lines = self.img_width

        min_lpf = lines / (self.fps * 2)
        max_lpf = lines / (self.fps * 5)
        self.lines_per_frame = randint(max_lpf, min_lpf + 1)

        coordinates = []
        if direction in ["ud", "du"]:
            for c in range(0, self.img_height, self.lines_per_frame):
                coordinates.append([slice(c, c+self.lines_per_frame),
                                    slice(0, self.img_width + 1)])
        else:
            for r in range(0, self.img_width, self.lines_per_frame):
                coordinates.append([slice(0, self.img_height + 1),
                                    slice(r, r+self.lines_per_frame)])

        self.coordinates = np.array(coordinates)
        if direction in ["du", "rl"]:
            self.coordinates = self.coordinates[::-1]


class ConvertChange(BackgroundChange):
    """
    Gradually change the current color to target color.
    First calculates the deltas per channel and
    divides this delta by the number of frames it should take.
    """
    def __init__(self, fps, img_shape, target_color, current_color):
        super().__init__(fps, img_shape, target_color, current_color)
        min_frames = self.fps * 2
        max_frames = self.fps * 5
        self.frames = randint(min_frames, max_frames+1)

        # B G R
        deltas = (target_color[0] - current_color[0],
                  target_color[1] - current_color[1],
                  target_color[2] - current_color[2])
        self.change_per_frame = np.array(deltas)/self.frames
        self.pseudo_frame = np.zeros((self.img_height, self.img_width, 3), np.float16)
        self.pseudo_frame[:, :] = self.current_color[:3]

    def next_step(self, frame):
        if self.frame < self.frames:
            self.pseudo_frame[:, :] += self.change_per_frame
            self.pseudo_frame[self.pseudo_frame > 255] = 255
            frame = self.pseudo_frame.round().astype(np.uint8)
            self.frame += 1
        else:
            # cleanup, finish the job
            frame[:] = self.target_color[:3]
            self.working = False
            self.finished = True
        return frame


class PolygonChange(BackgroundChange):
    """
    Creates a random polygon of 4 corners and then gradually sets its coordinates
    to take the entire frame.
    """
    def __init__(self, fps, img_shape, target_color, current_color):
        super().__init__(fps, img_shape, target_color, current_color=current_color)
        min_frames = self.fps * 1
        max_frames = self.fps * 2
        self.frames = randint(min_frames, max_frames+1)

        # B G R
        self.pseudo_points = np.array([
            np.random.randint(0, round(self.img_width/2)),
            np.random.randint(0, round(self.img_height/2)),

            np.random.randint(round(self.img_width / 2), self.img_width),
            np.random.randint(0, round(self.img_height / 2)),

            np.random.randint(round(self.img_width / 2), self.img_width),
            np.random.randint(round(self.img_height / 2), self.img_height),

            np.random.randint(0, round(self.img_width / 2)),
            np.random.randint(round(self.img_height / 2), self.img_height),
        ], dtype=np.float16)

        goals = [
            0,
            0,
            self.img_width,
            0,
            self.img_width,
            self.img_height,
            0,
            self.img_height
        ]

        deltas = np.array(goals) - np.array(self.pseudo_points)
        self.change_per_frame = np.array(deltas/self.frames, np.float16)
        self.shape = Polygon(list(np.int32(self.pseudo_points[0:2])),
                             list(np.int32(self.pseudo_points[2:])),
                             target_color)

    def next_step(self, frame):
        if self.frame < self.frames:
            frame[:] = self.current_color[:3]
            self.shape.draw(frame)
            self.pseudo_points += self.change_per_frame
            self.shape.set_coordinates(self.pseudo_points.round().astype(np.int32))
            self.frame += 1
        else:
            # cleanup, finish the job
            frame[:] = self.target_color[:3]
            self.working = False
            self.finished = True
        return frame


class RandomNoiseChange(BackgroundChange):
    """
    Creates frames of random color noise before chaning to the target color.
    Some frames are marked as 'flash_frames', which are special frames where
    the noise remains static.
    """
    def __init__(self, fps, img_shape, target_color):
        super().__init__(fps, img_shape, target_color)
        min_frames = self.fps * 3
        max_frames = self.fps * 6
        self.frames = randint(min_frames, max_frames+1)
        self.flash_frames = []
        if choice([True, True]):
            self.flash_frames = randint(0,
                                        self.frames,
                                        randint(round(self.fps/2), self.fps*2)
                                        )

    def __repr__(self):
        return "BackgroundChange of type %s. To %r From %r. Do flash = %r" \
               % (self.__class__.__name__,
                  self.target_color,
                  self.current_color,
                  self.flash_frames)

    def next_step(self, frame):
        if self.frame < self.frames:
            if self.frame not in self.flash_frames:
                frame = randint(0, 256, (self.img_height, self.img_width, 3), dtype=np.uint8)
            self.frame += 1
        else:
            # cleanup, finish the job
            frame[:] = self.target_color[:3]
            self.working = False
            self.finished = True
        return frame
