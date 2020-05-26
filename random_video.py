import argparse
import time
from taor.randomvideo import random_video

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Create random videos. The --seed argument can be used to generate'
                    'consistent results. By default the name of the video will contain the epoch'
                    'time of generation, otherwise --image_path can be used to overwrite this.'
    )
    parser.add_argument("-s", "--seed",
                        help="Initialize numpy with a given seed. "
                             "Can be used to obtain consistent results.",
                        type=int)
    parser.add_argument("-i", "--image_path",
                        help="Name of the file to create. "
                             "Epoch time is used as filename if -i is not specified.")
    parser.add_argument("-d", "--debug",
                        help="Enter DEBUG mode.",
                        action="store_true")
    parser.add_argument("-q", "--quantity",
                        help="Quantity of videos to generate. Default is 1."
                             "If --seed is set, the seed is used for the first video "
                             "and then 1 is added for each one of the following.",
                        type=int,
                        default=1)
    parser.add_argument("-f", "--frames",
                        help="Quantity of video frames to generate. "
                             "Default of 24*60*2 == 2880, for a 2 minutes video at 24 FPS.",
                        type=int,
                        default=24*60*2)
    args = parser.parse_args()

    seed = args.seed
    image_path = args.image_path
    frames = args.frames
    for i in range(args.quantity):
        if args.seed:
            seed = args.seed + i
            pre = args.image_path or "./results/" + str(int(time.time()))
            image_path = pre + "_seed%d.avi" % seed
        elif args.quantity > 1:
            pre = args.image_path or "./results/" + str(int(time.time()))
            image_path = pre + "_number%d.avi" % i
        else:
            pre = args.image_path or "./results/" + str(int(time.time()))
            image_path = pre + ".avi"

        random_video(file_name=image_path,
                     debug=args.debug,
                     seed=seed,
                     total_frames=frames)
