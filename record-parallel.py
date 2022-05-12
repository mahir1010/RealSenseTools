from ctypes import c_bool
import pyrealsense2 as rs
import json
import time
import multiprocessing
import os
import sys

if len(sys.argv) != 3:
    print('Usage python record-parallel.py <root_folder> <cfg>')
    exit()

root = sys.argv[1]
cfg=json.load(open(sys.argv[2],'r'))


time_stamp = time.strftime("%m%d%y-%H%M")
os.makedirs(os.path.join(root,time_stamp),exist_ok=True)

WARMUP_DELAY=5
system = rs.context()
master=None
slaves=[]
BURST_MODE=cfg['burst_mode']
TARGET_FRAME_RATE=cfg['target_slave_framerate']
NATIVE_FRAME_RATE=int(cfg['native_frame_rate'])
resolution=(int(cfg['target_slave_resX']),int(cfg['target_slave_resY']))

for i in range(len(system.devices)):
    if cfg["master"]==system.devices[i].get_info(rs.camera_info.serial_number):
        master=system.devices[i]
        sensor=master.first_depth_sensor()
        #We do not use the master camera to collect data.
        #To minimize latency, we set exposure very low (1ms)
        c_sensor=master.first_color_sensor()
        c_sensor.set_option(rs.option.enable_auto_exposure, 0)
        sensor.set_option(rs.option.enable_auto_exposure, 0)
        sensor.set_option(rs.option.exposure, 1000)
        sensor.set_option(rs.option.inter_cam_sync_mode,1)
    else:
        slaves.append(system.devices[i])
        roi_device=system.devices[i].first_roi_sensor()
        roi=roi_device.get_region_of_interest()
        # ROI for autoexposure for slave cameras.
        roi.min_x=290
        roi.min_y=270
        roi.max_x=370
        roi.max_y=310
        roi_device.set_region_of_interest(roi)
        sensor=slaves[-1].first_depth_sensor()
        c_sensor=slaves[-1].first_color_sensor()
        c_sensor.set_option(rs.option.enable_auto_exposure, 1)
        sensor.set_option(rs.option.enable_auto_exposure, 1)
        sensor.set_option(rs.option.inter_cam_sync_mode,BURST_MODE+3) # Add 3 to get inter_cam_sync_mode

#Master Camera setup

def configure_slaves(slave,flag):
    try:
        slave_pipeline=rs.pipeline()
        slave_cfg=rs.config()
        slave_cfg.enable_device(slave)
        slave_cfg.enable_stream(rs.stream.depth, *(resolution), rs.format.z16, NATIVE_FRAME_RATE)
        slave_cfg.enable_stream(rs.stream.color, *(resolution), rs.format.bgr8, 60) #RGB at 60Hz
        slave_cfg.enable_record_to_file(f"./{time_stamp}/{slave}.bag")
        while not flag.value:
            pass
        slave_pipeline.start(slave_cfg)
        while True:
            pass
    except:
        print(slave,"Stopped") 
    finally:
        slave_pipeline.stop()
        

if __name__=="__main__":
    running=multiprocessing.Value(c_bool,False)
    try:
        master_pipeline=rs.pipeline()
        master_cfg=rs.config()
        master_cfg.enable_device(master.get_info(rs.camera_info.serial_number))
        master_cfg.enable_stream(rs.stream.depth, 424,240, rs.format.z16, int(TARGET_FRAME_RATE//BURST_MODE) if BURST_MODE!=0 else TARGET_FRAME_RATE)
        master_pipeline.start(master_cfg)
        time.sleep(1)
        running.value=True
        for slave in slaves:
            p=multiprocessing.Process(target=configure_slaves,args=(slave.get_info(rs.camera_info.serial_number),running))
            p.start()
        for i in range(WARMUP_DELAY,0,-1):
            print(f"\rStart session in {i}",end='')
            time.sleep(1)
        print('')
        print("Recording Started")
        print('Use ctrl+c to stop. Any other method will corrupt bag files.')
        p.join()
    except:
        print("Master stopped")
    finally:
        master_pipeline.stop()
