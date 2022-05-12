import json
import math
import os
import pickle as pk
import sys
import traceback

import cv2
import numpy as np
import pyrealsense2 as rs

# This script converts bag files for all cameras to mp4. It also aligns the depth data with the RGB and saves it as a pickled numpy array of dimension HxW
# The script duplicates last framed when frame-drop is encountered to ensure alignment.
# Frame drop information can be inferred from the time-stamp csv.
# Folder Structure
# root
#  - 137322076445.bag
#  - 138422073715.bag
#  - 137322076528.bag



if len(sys.argv) != 2:
    print('Usage python convert_bag.py <root_folder>')
    exit()
root = sys.argv[1]

# Change names to your cameras.
cameras = ['137322076445', '138422073715', '137322076528']


params = json.load(open('cfg.json', 'r'))
params['resolution'] = (int(params['target_slave_resX']),
                        int(params['target_slave_resY']))
FRAME_RATE = params['target_slave_framerate']
FRAME_DIFF = 1000/FRAME_RATE


EXTRACT_FRAME_AT = 15
EXTRACT = False  # Extract frames at every 'EXTRACT_FRAME_AT' step

MEDIAN_BLUR = False
SHOW_DEPTH = False


for index, camera in enumerate(cameras):
    if EXTRACT:
        os.makedirs(os.path.join(root, camera), exist_ok=True)
    image_folder = os.path.join(root, camera)

    # Frame Alignment and depth filtering
    align = rs.align(rs.stream.color)
    spatial = rs.spatial_filter()
    hole_filling = rs.hole_filling_filter()

    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_device_from_file(os.path.join(root, f"{camera}.bag"), False)
    config.enable_stream(rs.stream.depth)
    config.enable_stream(rs.stream.color)
    pipeline.start(config)
    pipeline.get_active_profile().get_device().as_playback().set_real_time(False)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer_color = cv2.VideoWriter(os.path.join(
        root, f"{camera}_color.mp4"), fourcc, FRAME_RATE, params["resolution"])
    aligned_depth = open(os.path.join(root, f"{camera}.depth"), 'wb')
    count = 0
    if SHOW_DEPTH:
        video_writer_depth = cv2.VideoWriter(os.path.join(
            root, f"{camera}_depth.mp4"), fourcc, FRAME_RATE, params["resolution"])
    frame_no = -1
    timestamp = -1
    time_stamp_file = open(os.path.join(root, f"{camera}.csv"), 'w')
    prev_frame = None
    start_ts = None
    while True:
        try:
            frame = pipeline.wait_for_frames()
            if frame.get_frame_number() <= frame_no:
                continue
            write_count = 1
            if math.fabs(frame.timestamp-timestamp)-3 > FRAME_DIFF:
                write_count = round((frame.timestamp-timestamp)/FRAME_DIFF)
            if prev_frame:
                if start_ts == None:
                    start_ts = timestamp
                print(f"\r{camera}:{(timestamp-start_ts)/1000}", end='')
                depth_frame = prev_frame.get_depth_frame()
                depth_frame = spatial.process(depth_frame)
                depth_frame = hole_filling.process(depth_frame)
                depth_image = np.asanyarray(depth_frame.get_data())
                color_frame = prev_frame.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data())
                if MEDIAN_BLUR:
                    color_image = cv2.medianBlur(color_image, 3)
                if SHOW_DEPTH:
                    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(
                        depth_image, alpha=.2, beta=0.1), cv2.COLORMAP_HOT)
                    for k in range(write_count):
                        video_writer_depth.write(depth_colormap)
                    cv2.imshow("depth", depth_colormap)
                for k in range(write_count):
                    pk.dump(depth_image, aligned_depth)
                    time_stamp_file.write(str(prev_frame.timestamp)+"\n")
                    video_writer_color.write(color_image)
                    count += 1
                    if EXTRACT and count % EXTRACT_FRAME_AT == 0:
                        cv2.imwrite(os.path.join(
                            image_folder, f"{count}.png"), color_image)
                cv2.imshow("color", color_image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    video_writer_color.release()
                    video_writer_depth.release()
                    break
            del prev_frame
            prev_frame = align.process(frame)
            timestamp = frame.timestamp
            frame_no = frame.get_frame_number()
        except:
            print(traceback.format_exc())
            video_writer_color.release()
            if SHOW_DEPTH:
                video_writer_depth.release()
            break
