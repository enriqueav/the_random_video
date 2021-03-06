# The Random Video (alpha)

## [WIP]

Video version of [The Artist of Random](https://github.com/enriqueav/the_artist_of_random/). 

![example](https://raw.githubusercontent.com/enriqueav/the_random_video/master/static/example.gif)

## More Example Videos in Youtube

[![example1](https://img.youtube.com/vi/SNJRu4FNoVw/0.jpg)](https://www.youtube.com/watch?v=SNJRu4FNoVw)

[![example2](https://img.youtube.com/vi/X2AvT2Pb6C0/0.jpg)](https://www.youtube.com/watch?v=X2AvT2Pb6C0)

## How to clone and install

Clone the repository

```sh
git clone https://github.com/enriqueav/the_random_video.git
cd the_random_video
```

You might need to install the dependencies

```sh
pip install -r requirements.txt
```

## Generate a single random video

To create a single 60 seconds random video:

```
$ python3 random_video.py
```

The command will print the general configuration of the video file and the timeline of the events:

```
$ python random_video.py 
Creating Video
  - file_name: ./examples/1590319663.avi
  - img_width: 1280
  - img_height: 720
  - total_frames: 2880
  - seed: None
  - generators_quantity: 1
Created the following Generator(s):
<class 'taor.generators.Lasso'>
=== Timeline ===
0:00:00 : Start Video 
0:00:30 : BackgroundChange of type ConvertChange. Target color: (162, 31, 238) 
0:00:34 : Finished BG Change 
0:00:51 : Effect Started: PostEffect of type Mirror for 12 seconds 
0:01:03 : Effect finished: PostEffect of type Mirror for 12 seconds 
0:01:06 : BackgroundChange of type GridChange. Target color: (44, 239, 73) 
0:01:06 : Finished BG Change 
0:01:35 : Effect Started: PostEffect of type ColorThreshold for 43 seconds 
0:01:40 : BackgroundChange of type PolygonChange. Target color: (193, 116, 178) 
0:01:42 : Finished BG Change 
0:02:00 : End Video. Saved to ./examples/1590319663.avi 
```

## Description of the architecture

So far there are 3 different components of the video animation

### Generators

Responsible for the creation of shapes (artifacts) follow a certain geometric pattern,
usually driven by random forces. The sizes and colors of the shapes can also change over the time.
Right now, as the proof of concept, they are only generating simple shapes like circles or rectangles,
in new generators they could create any type of complex layer.
Here are some examples:

#### Lasso Generator

![lasso](https://raw.githubusercontent.com/enriqueav/the_random_video/master/static/lasso.gif)

#### Explosion Generator

![explosion](https://raw.githubusercontent.com/enriqueav/the_random_video/master/static/explosion.gif)


### Background Changes

The background is always a plain BGR color. 
There are several methods to change from the current color to the next.
Here are some examples:

#### Curtain Background Change

![curtain](https://raw.githubusercontent.com/enriqueav/the_random_video/master/static/curtain.gif)

#### Random Pixel Change

![randompixel](https://raw.githubusercontent.com/enriqueav/the_random_video/master/static/randompixel.gif)

### Post Effects

Effects that are applied to the finalized frame after drawing artifacts 
and background changes happening.
Here are some examples:

#### Mirror Effect

![mirror](https://raw.githubusercontent.com/enriqueav/the_random_video/master/static/mirror.gif)

#### To Grayscale Effect

![grayscale](https://raw.githubusercontent.com/enriqueav/the_random_video/master/static/grayscale.gif)


## Advanced use 

There are several arguments you can pass to the command

```
$ python3 random_video.py -h
usage: random_video.py [-h] [-s SEED] [-i IMAGE_PATH] [-d] [-q QUANTITY]
                       [-f FRAMES]

Create random videos. The --seed argument can be used to generateconsistent
results. By default the name of the video will contain the epochtime of
generation, otherwise --image_path can be used to overwrite this.

optional arguments:
  -h, --help            show this help message and exit
  -s SEED, --seed SEED  Initialize numpy with a given seed. Can be used to
                        obtain consistent results.
  -i IMAGE_PATH, --image_path IMAGE_PATH
                        Name of the file to create. Epoch time is used as
                        filename if -i is not specified.
  -d, --debug           Enter DEBUG mode.
  -q QUANTITY, --quantity QUANTITY
                        Quantity of videos to generate. Default is 1.If --seed
                        is set, the seed is used for the first video and then
                        1 is added for each one of the following.
  -f FRAMES, --frames FRAMES
                        Quantity of video frames to generate. Default of
                        24*60, for a 60 seconds video at 24 FPS.
```

### Advanced example

Generate 10 videos of 60 seconds (1440 frames) each, starting with the seed 771 
and save them in a new directory, with the fixed prefix `10videos` for the name.
Execute it in debug mode:

```commandline
mkdir results/seed771
python random_video.py --seed 771 \
            --debug --quantity 10 \
            --frames 1440 \
            --image_path results/seed771/10videos
```

After the process finishes, it will result in something like this:

```commandline
$ ls -1 results/seed771
10videos_seed771.avi
10videos_seed772.avi
10videos_seed773.avi
10videos_seed774.avi
10videos_seed775.avi
10videos_seed776.avi
10videos_seed777.avi
10videos_seed778.avi
10videos_seed779.avi
10videos_seed780.avi
```

### Ideas, TODO

* Input a music file and use [librosa](https://github.com/librosa/librosa) to analyze it 
and schedule the events according to the changes in the beat.
* Add some kind of neural style transfer as post effect.
* Allow several generators at the same time, or sequentially

### What's new in version 0.1: *2020-05-26*

* Initial creation of the repository. Many changes are pending.
* Replaced Pillow with OpenCV, to be able to export to Video
* Draw only generators, not individual shapes
* Created the division of BG change, Generators and Post Effects
* Uploaded the actual video generation code based on "the artist of random"