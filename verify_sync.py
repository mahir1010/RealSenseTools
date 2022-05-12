import glob
import os
import sys

import cv2
import numpy as np
import pandas as pd

# Press Left and Right Arrows to traverse
# Press 'd'/'D' to delete all images that are not valid for annotations.

# Camera IDs
# Folder Structure:
# Camera-ID/*.png | Synchronized frames should have same the same name in each folder

if len(sys.argv) != 2:
    print('Usage python verify_sync.py <root_folder>')
    exit()
root = sys.argv[1]


camera_map = pd.read_csv('camera_map.csv')

folders = camera_map['Camera'].to_list()
files = [os.path.basename(f) for f in glob.glob(
    os.path.join(root, folders[0])+'/*.png')]
files = list(set(files))
files.sort()
count = len(files)
idx = 0
incr = True
run_flag = True


# Calculate Optimal Resize factor
MaxWidth = 512
dims = [cv2.imread(os.path.join(root, cam, files[0])).shape[:2]
        for cam in folders]
resize = [(int(d[0]/(d[1]/512)), 512) for d in dims]
order = []
for unique_dim in set(resize):
    order.append([])
    for j, dim in enumerate(resize):
        if dim == unique_dim:
            order[-1].append(j)
output_size = (sum([d[0] for d in set(resize)]),
               512*max([len(o) for o in order]), 3)

mark_for_deletion = []

while run_flag:
    print(f'{idx}/{count}')
    images = [cv2.imread(os.path.join(root, cam, files[idx]))
              for cam in folders]
    # Resize and concatenate images
    if idx in mark_for_deletion:
        images[0] = cv2.putText(images[0], text="Deleted", org=(
            20, 60), fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=1.0, color=(0, 0, 255), thickness=1)
    images[0] = cv2.putText(images[0], text=files[idx], org=(
        20, 20), fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=1.0, color=(255, 255, 255), thickness=1)
    image = np.zeros(output_size, dtype=np.uint8)
    images = [cv2.resize(img, (resize_factor[1], resize_factor[0]))
              for img, resize_factor in zip(images, resize)]
    offset = 0
    for dim, indices in zip(set(resize), order):
        for i, index in enumerate(indices):
            image[offset:offset+dim[0],
                  (i*dim[1]):dim[1]+(i*dim[1]), :] = images[index]
        offset += dim[0]

    cv2.imshow('frame', image)

    key = cv2.waitKey(-1) & 0xff
    if key in [ord('d'), ord('D')]:
        if idx in mark_for_deletion:
            mark_for_deletion.remove(idx)
        else:
            mark_for_deletion.append(idx)

    elif key == 81:
        incr = False
        idx = idx-1 if idx > 0 else count-1
    elif key == 83:
        incr = True
        idx = idx+1 if idx < count-1 else 0
    elif key == 27:
        run_flag = False

for cam in folders:
    for idx in mark_for_deletion:
        print(files[idx], "deleted")
        os.remove(os.path.join(root, cam, files[idx]))
