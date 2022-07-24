# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

# June 3, 2022
# Add on collage photo creater by Khoa Le Tien

"""Generate style collage of images using pretrained network pickle."""

import os
import re
from typing import List

import click
import dnnlib
import numpy as np
import PIL.Image
import torch

import cv2
import random

import legacy

#----------------------------------------------------------------------------

def num_range(s: str) -> List[int]:
    '''Accept either a comma separated list of numbers 'a,b,c' or a range 'a-c' and return as a list of ints.'''

    range_re = re.compile(r'^(\d+)-(\d+)$')
    m = range_re.match(s)
    if m:
        return list(range(int(m.group(1)), int(m.group(2))+1))
    vals = s.split(',')
    return [int(x) for x in vals]

#----------------------------------------------------------------------------

@click.command()
@click.option('--network', 'network_pkl', help='Network pickle filename', required=True)
@click.option('--seeds', 'seeds', type = num_range, help = 'List of random seeds to interpolation', required = True)
@click.option('--num_row', 'num_row', type = int, help = 'Number of row'   , default = 4, show_default = True)
@click.option('--num_col', 'num_col', type = int, help = 'Number of column', default = 7, show_default = True)
@click.option('--trunc', 'truncation_psi', type=float, help='Truncation psi', default=1, show_default=True)
@click.option('--noise-mode', help='Noise mode', type=click.Choice(['const', 'random', 'none']), default='const', show_default=True)
@click.option('--outdir', type=str, required=True)
def generate_style_interpolation_video(
    network_pkl: str,
    seeds: List[int],
    num_row: int,
    num_col: int,
    truncation_psi: float,
    noise_mode: str,
    outdir: str
):
    """Generate style collage of images using pretrained network pickle."""

    print('Loading networks from "%s"...' % network_pkl)
    device = torch.device('cuda')
    with dnnlib.util.open_url(network_pkl) as f:
        G = legacy.load_network_pkl(f)['G_ema'].to(device) # type: ignore

    os.makedirs(outdir, exist_ok=True)

    print('Generating W vectors ...')
    seeds = list(set(seeds))
    all_z = np.stack([np.random.RandomState(seed).randn(G.z_dim) for seed in seeds])
    all_w = G.mapping(torch.from_numpy(all_z).to(device), None)
    w_avg = G.mapping.w_avg
    all_w = w_avg + (all_w - w_avg) * truncation_psi
    w_dict = {seed: w for seed, w in zip(seeds, list(all_w))}

    cell_width  = G.img_resolution
    cell_height = G.img_resolution
    collage_width  = cell_width  * num_col
    collage_height = cell_height * num_row
    canvas = np.zeros((collage_height, collage_width, 3), np.uint8)



    print('Generating style collage images ...')
    for row_index in range(num_row):
        x = row_index * cell_height
        for col_index in range(num_col):
            seed  = seeds[row_index * num_col + col_index]
            w     = w_dict[seed] 
            image = G.synthesis(w[np.newaxis], noise_mode = noise_mode) 
            image = (image.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
            image = image[0].cpu().numpy()

            y = col_index * cell_width
            canvas[x:x + cell_height:, y:y + cell_width:, ::] = image

    print('Saving collage ...')
    os.makedirs(outdir, exist_ok = True)
    file_name = f"{outdir}/Style GAN Collage {num_row} by {num_col}.png"
    PIL.Image.fromarray(canvas, 'RGB').save(file_name)

#----------------------------------------------------------------------------

if __name__ == "__main__":
    generate_style_interpolation_video() # pylint: disable=no-value-for-parameter

#----------------------------------------------------------------------------
