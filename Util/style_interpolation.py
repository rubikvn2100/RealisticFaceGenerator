# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

# May 31, 2022
# Add on Interpolation by Khoa Le Tien

"""Generate style interpolation images using pretrained network pickle."""

import os
import re
from typing import List

import click
import dnnlib
import numpy as np
import PIL.Image
import torch

import cv2

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
@click.option('--step', 'step', type = int, help = 'number of interpolation step', default = 5, show_default = True)
@click.option('--FPS', 'FPS', type = int, help = 'number of Frames Per Second', default = 30, show_default = True)
@click.option('--export_image', 'export_image', type = bool, help = 'display images', default = False, show_default = True)
@click.option('--trunc', 'truncation_psi', type=float, help='Truncation psi', default=1, show_default=True)
@click.option('--noise-mode', help='Noise mode', type=click.Choice(['const', 'random', 'none']), default='const', show_default=True)
@click.option('--outdir', type=str, required=True)
def generate_style_interpolation(
    network_pkl: str,
    seeds: List[int],
    step: int,
    FPS: int,
    export_image: bool, 
    truncation_psi: float,
    noise_mode: str,
    outdir: str
):
    """Generate style interpolation images using pretrained network pickle.

    Examples:

    \b
    python style_interpolation.py --seeds=164,218 \\
        --network=https://nvlabs-fi-cdn.nvidia.com/stylegan2-ada-pytorch/pretrained/metfaces.pkl
    """
    print('Loading networks from "%s"...' % network_pkl)
    device = torch.device('cuda')
    with dnnlib.util.open_url(network_pkl) as f:
        G = legacy.load_network_pkl(f)['G_ema'].to(device) # type: ignore

    os.makedirs(outdir, exist_ok=True)

    print('Generating W vectors...')
    all_seeds = list(set(seeds))
    all_z = np.stack([np.random.RandomState(seed).randn(G.z_dim) for seed in all_seeds])
    all_w = G.mapping(torch.from_numpy(all_z).to(device), None)
    w_avg = G.mapping.w_avg
    all_w = w_avg + (all_w - w_avg) * truncation_psi
    w_dict = {seed: w for seed, w in zip(all_seeds, list(all_w))}

    print('Generating style-interpolation images...')

    from_seed = seeds.pop(0)
    w     = w_dict[from_seed] 
    image = G.synthesis(w[np.newaxis], noise_mode = noise_mode) 
    image = (image.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
    result_list = [(from_seed, None, None, image[0].cpu().numpy())]
    while seeds:
        to_seed = seeds.pop(0)
        print(f"Generate interpolation for image {from_seed}-{to_seed} ...")
        for i in range(1, step):
            w = (w_dict[from_seed] * (step - i) + w_dict[to_seed] * i) / step
            image = G.synthesis(w[np.newaxis], noise_mode=noise_mode)
            image = (image.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
            result_list.append((from_seed, to_seed, i, image[0].cpu().numpy()))
        from_seed = to_seed 

        w     = w_dict[from_seed] 
        image = G.synthesis(w[np.newaxis], noise_mode = noise_mode) 
        image = (image.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
        result_list.append((from_seed, None, None, image[0].cpu().numpy()))

    print('Saving video...')
    file_name = f"{outdir}/Interpolation Style Gan {step} step {FPS} FPS.avi"
    video_width  = G.img_resolution
    video_height = G.img_resolution
    video = cv2.VideoWriter(file_name, cv2.VideoWriter_fourcc(*'MJPG'), FPS, (video_width, video_height))
    for _, _, _, image in result_list:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        video.write(image)
    video.release()

    if not export_image:
        return

    print('Saving images...')
    os.makedirs(outdir, exist_ok = True)
    for i, (from_seed, to_seed, current_step, image) in enumerate(result_list):
        if current_step is None:
            file_name = f"{outdir}/{str(i).zfill(5)} image {from_seed}.png"
            PIL.Image.fromarray(image, 'RGB').save(file_name)
        else:
            file_name = f"{outdir}/{str(i).zfill(5)} interpolate {from_seed}-{to_seed} {i} of {step}.png"
            PIL.Image.fromarray(image, 'RGB').save(file_name)
#----------------------------------------------------------------------------

if __name__ == "__main__":
    generate_style_interpolation() # pylint: disable=no-value-for-parameter

#----------------------------------------------------------------------------
