#!/usr/bin/env python
# GIMP Python-Fu: Texture Pipeline for brick_red @ 1024px
# Usage: gimp -i -b 'python-fu-eval -s "output/scripts/gimp/texture_brick_red_1024.py"' -b '(gimp-quit 0)'
from gimpfu import *

def process_brick_red():
    img = pdb.gimp_file_load("output/textures/brick_red_1024.png", "output/textures/brick_red_1024.png")
    d = pdb.gimp_image_get_active_drawable(img)
    pdb.gimp_image_scale_full(img, 1024, 1024, INTERPOLATION_LANCZOS)
    pdb.plug_in_unsharp_mask(img, d, 3.0, 0.5, 0)
    pdb.gimp_drawable_hue_saturation(d, HUE_RANGE_ALL, 0, 0, 15, 0)
    n = pdb.gimp_layer_copy(d, True)
    pdb.gimp_image_insert_layer(img, n, None, -1)
    pdb.plug_in_emboss(img, n, 315, 45.0, 7, True)
    pdb.file_png_save(img, d, "output/textures/brick_red_processed.png", "brick_red", 0,9,1,1,1,1,1)
    pdb.gimp_image_set_active_layer(img, n)
    pdb.file_png_save(img, n, "output/textures/brick_red_normal.png", "brick_red_n", 0,9,1,1,1,1,1)
    pdb.gimp_image_delete(img)

process_brick_red()
