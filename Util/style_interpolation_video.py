# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

# May 31, 2022
# Add on Interpolation by Khoa Le Tien

"""Generate style interpolation video using pretrained network pickle."""

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

def create_seed_mapping(N_row: int, N_col: int, N_wanted_elem: int, elem_list: List[int], state: int) -> List[List[List[int]]]:
    '''Create a grid mapping of element sequence 
    such that no two element in any two sequence have the same value and index'''

    N_wanted_list = N_row * N_col

    all_list      = []
    pair_set      = set()
    location_dict = {elem: [] for elem in elem_list}
    for list_id in range(N_wanted_list):
        row_id = int(list_id / N_col)
        col_id =     list_id % N_col
        new_list = []
        for elem_id in range(N_wanted_elem):
            non_candidates = set(new_list + [lst[len(new_list)] for lst in all_list])
            candidates = set(elem_list).difference(non_candidates)
            candidates = list(candidates)

            random.Random(state).shuffle(candidates)
            candidates_distance_to_closet = []
            for candidate in candidates:
                min_distance = 10 ** 9
                for r, c, e in location_dict[candidate]:
                    distance     = ((row_id - r) ** 2 + (col_id - c) ** 2 + (elem_id - e) ** 2) ** 0.5
                    min_distance = min(min_distance, distance)

                candidates_distance_to_closet.append((candidate, min_distance))

            candidate_with_farthest_distance = None
            farthest_distance                = 0

            for candidate, distance in candidates_distance_to_closet:
                previous_elem = new_list[-1] if new_list else -1
                if not ((previous_elem, candidate) in pair_set):   
                    if distance > farthest_distance:                     
                        candidate_with_farthest_distance = candidate
                        farthest_distance                = distance
                    if farthest_distance == 10 ** 9:
                        break

            if new_list:
                if candidate_with_farthest_distance:
                    pair_set.add((new_list[-1], candidate_with_farthest_distance))
                    pair_set.add((candidate_with_farthest_distance, new_list[-1]))
                else: 
                    return None

            new_list.append(candidate_with_farthest_distance)
            location_dict[candidate_with_farthest_distance].append((row_id, col_id, elem_id))

        all_list.append(new_list)

    mapping = [[all_list[i * N_col + j] for j in range(N_col)] for i in range(N_row)]
    return mapping
  
#----------------------------------------------------------------------------  

def create_unique_seed_mapping(N_row: int, N_col: int, N_wanted_elem: int, elem_list: List[int], state: int) -> List[List[List[int]]]:
    '''Create a unique grid mapping of element sequence
    return None if not enough element'''

    if len(elem_list) < N_row * N_col * N_wanted_elem:
        return None

    random.Random(state).shuffle(elem_list)

    mapping = [[[None for _ in range(N_wanted_elem)] for _ in range(N_col)] for _ in range(N_row)]
    index = 0
    for i in range(N_row):
        for j in range(N_col):
            for k in range(N_wanted_elem):
                mapping[i][j][k] = elem_list[index]
                index += 1

    return mapping

#----------------------------------------------------------------------------

@click.command()
@click.option('--network', 'network_pkl', help='Network pickle filename', required=True)
@click.option('--seeds', 'seeds', type = num_range, help = 'List of random seeds to interpolation', required = True)
@click.option('--step', 'step', type = int, help = 'Number of interpolation step', default = 5, show_default = True)
@click.option('--FPS', 'FPS', type = int, help = 'Number of Frames Per Second', default = 30, show_default = True)
@click.option('--num_row', 'num_row', type = int, help = 'Number of row'   , default = 4, show_default = True)
@click.option('--num_col', 'num_col', type = int, help = 'Number of column', default = 7, show_default = True)
@click.option('--image_per_cell', 'image_per_cell', type = int, help = 'Number of image in a cell', default = 5, show_default = True)
@click.option('--trunc', 'truncation_psi', type=float, help='Truncation psi', default=1, show_default=True)
@click.option('--noise-mode', help='Noise mode', type=click.Choice(['const', 'random', 'none']), default='const', show_default=True)
@click.option('--outdir', type=str, required=True)
@click.option("--state", "state", type = int, help = "random state", default = 1, show_default = True)
def generate_style_interpolation_video(
    network_pkl: str,
    seeds: List[int],
    step: int,
    FPS: int,
    num_row: int,
    num_col: int,
    image_per_cell: int,
    truncation_psi: float,
    noise_mode: str,
    outdir: str,
    state: int
):
    """Generate style interpolation video using pretrained network pickle."""

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

    seed_mapping = create_unique_seed_mapping(num_row, num_col, image_per_cell, seeds, state)
    if seed_mapping is None:
        seed_mapping = create_seed_mapping(num_row, num_col, image_per_cell, seeds, state)
    
    if seed_mapping is None:
        print("Cannot create seed mapping, please retry or increase the number of seeds")
        return 

    cell_width  = G.img_resolution
    cell_height = G.img_resolution
    video_width  = cell_width  * num_col
    video_height = cell_height * num_row

    file_name = f"{outdir}/Interpolation Style GAN {num_row} by {num_col}, {step} step, {FPS} FPS, {image_per_cell} image per cell, state {state}.avi"
    video = cv2.VideoWriter(file_name, cv2.VideoWriter_fourcc(*'MJPG'), FPS, (video_width, video_height))

    total_frame = step * (image_per_cell - 1) + 1
    frame_count = 0

    pair_seed_mapping = [None, None]
    for k in range(image_per_cell):
        seed_mapping_k    = [[seed_mapping[i][j][k] for j in range(num_col)] for i in range(num_row)]
        pair_seed_mapping = [pair_seed_mapping[1], seed_mapping_k]
        frame = np.zeros((video_height, video_width, 3), np.uint8)

        if pair_seed_mapping[0] == None:
            w_list = []
            for i in range(num_row):
                for j in range(num_col):
                    w_list.append(w_dict[seed_mapping_k[i][j]])
            
            from_id = 0
            to_id   = 32
            images  = None
            while from_id < len(w_list):
                w_sub_list = torch.stack(w_list[from_id:min(to_id, len(w_list))])
                sub_images = G.synthesis(w_sub_list, noise_mode = noise_mode) 
                sub_images = (sub_images.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
                
                if images is None:
                    images = sub_images
                else:
                    images = torch.cat((images, sub_images), 0)

                from_id += 32
                to_id   += 32
        
            for i in range(num_row):
                for j in range(num_col):
                    image = images[i * num_col + j].cpu().numpy()
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    
                    x_cell = cell_width  * i
                    y_cell = cell_height * j
                    frame[x_cell:x_cell + cell_width:, y_cell:y_cell + cell_height:, ::] = image
            
            frame_count += 1
            print(f"Generating style-interpolation frame {frame_count}/{total_frame} ...")
            video.write(frame)
            continue

        for i in range(step):
            w_list = []
            for row in range(num_row):
                for col in range(num_col):
                    w_src = w_dict[pair_seed_mapping[0][row][col]]
                    w_dst = w_dict[pair_seed_mapping[1][row][col]]
                    w_list.append((w_src * (step - i) + w_dst * i) / step)

            from_id = 0
            to_id   = 32
            images  = None
            while from_id < len(w_list):
                w_sub_list = torch.stack(w_list[from_id:min(to_id, len(w_list))])
                sub_images = G.synthesis(w_sub_list, noise_mode = noise_mode) 
                sub_images = (sub_images.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
                
                if images is None:
                    images = sub_images
                else:
                    images = torch.cat((images, sub_images), 0)

                from_id += 32
                to_id   += 32

            for row in range(num_row):
                for col in range(num_col):
                    image = images[row * num_col + col].cpu().numpy()
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    
                    x_cell = cell_width  * row
                    y_cell = cell_height * col
                    frame[x_cell:x_cell + cell_width:, y_cell:y_cell + cell_height:, ::] = image
                        
            frame_count += 1
            print(f"\rGenerating style-interpolation frame {frame_count}/{total_frame} ...", end = '')
            video.write(frame)

        print()

    print("Releasing video ...")
    video.release()

#----------------------------------------------------------------------------

if __name__ == "__main__":
    generate_style_interpolation_video() # pylint: disable=no-value-for-parameter

#----------------------------------------------------------------------------
