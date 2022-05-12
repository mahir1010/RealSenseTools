import glob
import os
import sys

import cv2
import numpy as np

# Press Left and Right Arrows to traverse
# Press 'd'/'D' to delete all images if they are not valid for annotations.

# Camera IDs
# Folder Structure:
# Camera-ID/*.png | Synchronized frames should have same the same name in each folder

if len(sys.argv) != 2:
    print('Usage python verify_sync.py <root_folder>')
    exit()
root = sys.argv[1]

folders = ["137322076528", "138422073715",
           '137322076445', 'red', 'green', 'orange']
files = [os.path.basename(f) for f in glob.glob(
    os.path.join(root, folders[0])+'/*.png')]
files = list(set(files))
files.sort()
count = len(files)
idx = 0
incr = True
run_flag = True
exception_count = 0
while run_flag:
    print(f'{idx}/{count}')
    images = [cv2.imread(os.path.join(root, cam, files[idx]))
              for cam in folders]
    try:
        # Resize and concatenate images
        images[0] = cv2.putText(images[0], text=files[idx], org=(
            20, 20), fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=1.0, color=(255, 255, 255), thickness=1)
        image = np.concatenate(images[:3], axis=0)
        image2 = np.concatenate(images[3:], axis=0)
        image = cv2.resize(image, (image.shape[1]//2, image.shape[0]//2))
        image2 = cv2.resize(image2, (image2.shape[1]//3, image2.shape[0]//3))
        exception_count = 0
    except:
        idx += 1 if incr else -1
        exception_count += 1
        if exception_count >= count:
            print("All Files Deleted!!")
            run_flag = False
        continue
    cv2.imshow('frame', image)
    cv2.imshow('frame2', image2)
    key = cv2.waitKey(-1) & 0xff
    if key in [ord('d'), ord('D')]:
        print(files[idx], "deleted")
        for cam in folders:
            os.remove(os.path.join(root, cam, files[idx]))
    elif key == 81:
        incr = False
        idx = idx-1 if idx > 0 else count-1
    elif key == 83:
        incr = True
        idx = idx+1 if idx < count-1 else 0
    elif key == 27:
        run_flag = False
