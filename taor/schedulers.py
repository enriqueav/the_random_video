import datetime
from numpy.random import randint

from taor.bg_changes import BackgroundFactory
from taor.post_effects import PostEffectFactory


class ScheduledEffect(object):
    """
    Represents a post_effect and its initial and final frame numbers
    """
    def __init__(self, fps, initial_frame, effect):
        self.fps = fps
        self.initial_frame = initial_frame
        self.effect = effect
        self.final_frame = self.initial_frame + self.effect.get_frames()

    def __str__(self):
        return "Effect: %s to %s. %r" % \
               (str(datetime.timedelta(seconds=int(self.initial_frame/self.fps))),
                str(datetime.timedelta(seconds=int(self.final_frame/self.fps))),
                self.effect)

    def __lt__(self, other):
        return self.initial_frame < other.initial_frame

    def get_initial_frame(self):
        return self.initial_frame


class EffectScheduler(object):
    """
    Scheduler of post_effects.
    Calling next_effect with the current frame number returns the next ScheduledEffect
    """
    def __init__(self, FPS, min_effect_wait, max_effect_wait, img_height, img_width):
        self.FPS = FPS
        self.min_effect_wait = min_effect_wait
        self.max_effect_wait = max_effect_wait
        self.post_effect_factory = PostEffectFactory(self.FPS, (img_height, img_width))

    def next_effect(self, current_frame):
        delay = randint(self.FPS * self.min_effect_wait, self.FPS * self.max_effect_wait)
        start_time = current_frame + delay
        return ScheduledEffect(
            self.FPS,
            start_time,
            self.post_effect_factory.create_post_effect()
        )


class ScheduledBackgroundChange(object):
    """
    Represents a bg_change and its initial frame number
    """
    def __init__(self, time, bg_change):
        self.time = time
        self.bg_change = bg_change


class BackgroundChangeScheduler(object):
    """
    Scheduler of backgrouns changes.
    Calling next_change it returns the next change to be performed.
    It also keeps the track of the frame number in self.current_frame, so it's
    not necessary to pass the current number to next_change
    """
    def __init__(self, FPS, min_bg_change_wait, max_bg_change_wait, img_height, img_width):
        self.FPS = FPS
        self.current_frame = 0
        self.min_bg_change_wait = min_bg_change_wait
        self.max_bg_change_wait = max_bg_change_wait
        self.bg_change_factory = BackgroundFactory(FPS, (img_height, img_width))

    def next_change(self, current_color):
        delay = randint(self.FPS * self.min_bg_change_wait, self.FPS * self.max_bg_change_wait)
        start_time = self.current_frame + delay
        self.current_frame += delay
        return ScheduledBackgroundChange(
            time=start_time,
            bg_change=self.bg_change_factory.create_bg_change(current_color)
        )
