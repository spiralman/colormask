# ColorMask #

ColorMask is an application for creating masks from images suitable
for, primarily, screen printing. Masks can be picked based on color or
luminance (lightness).

## Getting Started ##

After launching ColorMask, pick the image you want to use from `File
-> Select Source...`, then click the `+` icon in the bottom left of
the window to create a new mask.

Each mask has two primary types of controls: the `Selection Mode` and
the `Halftone Mode`. The `Selection Mode` controls how colors are picked
from the image to make the mask, and the `Halftone Mode` allows gray
areas in the mask to be rendered as a sequence of black and white
dots.

## Selection Modes ##

The starting point for all the `Selection Modes` is the color that is
being selected. Once a color is selected, the different types of
`Selection Modes` control how the program decides whether other colors
are similar enough to be part of the mask or not.

It is best to chose a reference color from the image using the
color-picker tool. This can be accessed by clicking the color swatch
in the control dialog, clicking the magnifying-glass icon, then
clicking on the image in the area you want to be part of the mask.

All `Selection Modes` also have a `Falloff` control, which controls
how sharp the division is between the black and white areas of the
mask. A `Falloff` of 0 will produce very hard edges, while a value of
1 will produce very soft edges.

### Perceptual Selection Mode ###

`Perceptual` selection mode choses colors based on how closely the
human eye perceives them to be the same. This is the optimal mode to
use for selecting masks from color images.

Changing the `Color` slider controls how similar the *color* must be,
regardless of how light or dark it is, before it is part of the
mask. Lower numbers mean that colors have to be very similar, while
larger numbers mean they can be further apart. The `Luminance` slider
similarly controls how closely the lightness of a color must match.

### Luminance Selection Mode ###

`Luminance` selection mode choses colors based solely on the lightness
or darkness of the image. This mode is best for black and white
images, or images in which the shadows define the ares you want to
mask.

## Halftone Modes ##

The `Halftone Modes` control if and how gray areas are converted into
patterns of black and white which will give the appearance of
gradients when printed. If you don't want halftoning, you can select
`None` from the drop-down.

The `Dots` halftoning mode is the most traditional. It will convert
gray areas into a grid of dots, which are closer together the darker
the gray. Sliders let you control the base size of the dots, as well
as the angle of the grid and the sharpness of the dots. When creating
multiple masks to be printed together, it is important to select
different angles for each mask.
