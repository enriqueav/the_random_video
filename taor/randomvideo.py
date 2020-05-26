"""
randomvideo module.
"""
import datetime
import numpy as np
from numpy.random import choice, randint
from cv2 import VideoWriter, VideoWriter_fourcc

from taor.generators import GeneratorFactory
from taor.color_factory import ColorFactory
from taor.schedulers import BackgroundChangeScheduler, EffectScheduler

config = dict(
    FPS=24,  # Frames Per Seconds
    img_width=1280,
    img_height=720,
    max_effects=1,
    min_bg_change_wait=20,  # Minimum seconds before changing background
    max_bg_change_wait=60,  # Maximum seconds before changing background
    min_effect_wait=30,  # Minimum seconds for an effect to work
    max_effect_wait=60,  # Maximum seconds for an effect to work
    p_movement=[0.75, 0.12, 0.13],  # Probability of 0, 1 and -1 movement
)


def get_video(file_name, FPS, img_width, img_height):
    fourcc = VideoWriter_fourcc(*'MP42')
    return VideoWriter(file_name, fourcc, float(FPS), (img_width, img_height), True)


def get_canvas(img_height, img_width):
    color_factory = ColorFactory()
    current_color = color_factory.get_rgb_color()[:3]
    canvas = np.zeros((img_height, img_width, 3), np.uint8)
    canvas[:] = current_color
    return canvas, current_color


def get_movement(p_movement):
    movement_y = choice([None, 1, -1], p=p_movement)
    movement_x = choice([None, 1, -1], p=p_movement)
    return movement_y, movement_x


def print_to_timeline(fps, frame_number, message):
    print("%s : %s " % (
        str(datetime.timedelta(seconds=int(frame_number/fps))),
        message
        )
    )


def random_video(file_name=None, debug=False, seed=None, total_frames=None, generators_quantity=1):
    if seed:
        np.random.seed(seed)

    img_width = config['img_width']
    img_height = config['img_height']
    FPS = config['FPS']

    print("Creating Video")
    print("  - file_name: %s" % file_name)
    print("  - img_width: %d" % img_width)
    print("  - img_height: %s" % img_height)
    print("  - total_frames: %d" % total_frames)
    print("  - seed: %r" % seed)
    print("  - generators_quantity: %d" % generators_quantity)

    # Create all the Factories
    generator_factory = GeneratorFactory(max(img_height, img_width))
    bg_change_scheduler = BackgroundChangeScheduler(
        FPS, config['min_bg_change_wait'], config['max_bg_change_wait'], img_height, img_width
    )
    effect_scheduler = EffectScheduler(
        FPS, config['min_effect_wait'], config['max_effect_wait'], img_height, img_width
    )

    # Initialize the Canvas and set it to an initial random color
    canvas, current_color = get_canvas(img_height, img_width)
    video = get_video(file_name, FPS, img_width, img_height)

    # Global movement of artifacts
    movement_y, movement_x = get_movement(config['p_movement'])
    move_every_n_frames = randint(1, FPS+1)

    # Maximum number of repeated frames before relocating the generator's center
    max_repeated_frames = randint(FPS*1, FPS*4+1)

    generators = []
    for _ in range(generators_quantity):
        generators.append(generator_factory.create_generator())

    print("Created the following Generator(s):")
    for g in generators:
        print(type(g))
        if debug:
            print(g)

    if debug:
        print("max_repeated_frames = %d" % max_repeated_frames)
        print("Global Movement")
        print("  movement_x = %r" % movement_x)
        print("  movement_y = %r" % movement_y)
        print("  move_every_n_frames = %d" % move_every_n_frames)

    last_frame = canvas.copy()

    background_change = bg_change_scheduler.next_change(current_color)

    effects = []
    for _ in range(config['max_effects']):
        effects.append(effect_scheduler.next_effect(current_frame=0))
    effects.sort()

    should_redraw = True
    background = canvas.copy()
    change_happening = None

    effects_happening = []
    artifacts = []

    recycled_frames = 0
    repeated_consecutive_frames = 0
    ####################################################################################
    ####################################################################################
    # Start the show \(._.)/
    ####################################################################################
    ####################################################################################
    print("=== Timeline ===")
    print_to_timeline(FPS, 0, "Start Video")

    for frame_number in range(total_frames):
        last_index = len(artifacts)

        # Phase 0: Get the artifact to print on this frame
        for g in generators:
            artifacts.extend(g.generate())

        ############################
        # Phase I: Background change
        ############################
        if frame_number == background_change.time:
            change_happening = background_change.bg_change
            print_to_timeline(FPS, frame_number, background_change.bg_change)

        if change_happening and change_happening.is_working():
            background = change_happening.next_step(background)
            should_redraw = True
            if change_happening.has_finished():
                current_color = change_happening.get_final_color()
                background_change = bg_change_scheduler.next_change(current_color)
                print_to_timeline(FPS, frame_number, "Finished BG Change")
                change_happening = None
        # END OF Phase I

        ###################################################
        # Phase II: Deal with artifacts. Painting and Death
        ###################################################
        if should_redraw:
            frame = background.copy()
            initial_artifact = 0
        else:
            frame = last_frame
            initial_artifact = last_index
            recycled_frames += 1

        at_least_one_change = False
        should_redraw = False

        # Paint only the live artifacts that are inside the frame's boundaries
        for a in artifacts[initial_artifact:]:
            if not a.dead and a.will_paint((img_width, img_height)):
                if not a.painted:
                    at_least_one_change = True
                a.draw(frame)
                a.painted = True

        # Check for dead artifacts. The ones that reached their lifespan.
        # If found, we know we should redraw the next frame, as something has changed
        for a in artifacts:
            if not a.dead:
                a.age += 1
                if a.age >= a.lifespan:
                    a.dead = True
                    if a.painted and a.will_paint((img_width, img_height)):
                        at_least_one_change = True
                        should_redraw = True
        artifacts = [a for a in artifacts if not a.dead]

        if not at_least_one_change:
            repeated_consecutive_frames += 1
        else:
            repeated_consecutive_frames = 0
        # END OF Phase II

        ##########################
        # Phase III: Post Effects
        ##########################
        painted_frame = frame

        # Check if there is an effect starting this frame
        while len(effects) > 0 and effects[0].get_initial_frame() == frame_number:
            effects_happening.append(effects.pop(0))
            print_to_timeline(
                FPS, frame_number, "Effect Started: %r" % effects_happening[-1].effect
            )

        if len(effects_happening) > 0:
            painted_frame = frame.copy()

        effects_to_remove = []
        for index, happening in enumerate(effects_happening):
            # Get the frame after processing the effect
            painted_frame = happening.effect.next_step(painted_frame)
            # should_redraw = True
            if happening.effect.has_finished():
                print_to_timeline(FPS, frame_number, "Effect finished: %r" % happening.effect)
                effects.append(effect_scheduler.next_effect(current_frame=frame_number))
                effects_to_remove.append(index)

        effects_happening = [
            effect for effect_number, effect in enumerate(effects_happening)
            if effect_number not in effects_to_remove
        ]
        effects.sort()
        # END OF Phase III

        #########################################
        # Phase IV: General Movement of Artifacts
        # TODO: Create artifact move effects
        #########################################
        if (movement_x or movement_y) and frame_number % move_every_n_frames == 0:
            for a in artifacts:
                a.move_yx(movement_x, movement_y)
            # of course we need to redraw
            should_redraw = True

        # Shake things up if there are too many repeated frames
        if repeated_consecutive_frames > max_repeated_frames:
            dx = randint(0, img_width)
            dy = randint(0, img_height)
            generators[0].move_origin(dx, dy)
            repeated_consecutive_frames = 0
        # END OF Phase IV

        ########################################
        # Phase V: Actually Write Frame to Video
        ########################################
        video.write(painted_frame)
        last_frame = frame

    print_to_timeline(FPS, total_frames, "End Video. Saved to %s" % file_name)
    video.release()

    if debug:
        print("recycled_frames ", recycled_frames)
