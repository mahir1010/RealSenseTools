from urllib.parse import MAX_CACHE_SIZE
import pandas as pd
import os                                                                       
from multiprocessing import Pool
import sys

DEBUG=False
MAX_PROCESSES=10

# Output file names should not be the same as the input file name. At least the file extension should be different.

if len(sys.argv) != 3:
    print('Usage python clip_files.py <root_folder> <seconds>\nRoot Folder should contain sync.csv containing seek position for aligning each camera')
    exit()
root = sys.argv[1]
seconds = int(sys.argv[2])
try:
    camera_map=pd.read_csv('camera_map.csv')
    sync=pd.read_csv(os.path.join(root,'sync.csv'))
    if len(set(camera_map['Camera'].to_list()).intersection(sync['Camera'].to_list()))!=len(camera_map):
        raise Exception("Camera names not matching in camera_map.csv and sync.csv")
except Exception as e:
    print(e)
    exit()

base_command = 'ffmpeg -i {} -ss {} -t {} -crf 15 {}.mp4'

commands=[]                                                                           
for index,row in camera_map.iterrows():
    file_path=os.path.join(root,row['File'])
    if os.path.exists(file_path):
        commands.append(base_command.format(file_path,sync[sync['Camera']==row['Camera']]['Start'].values[0],seconds,os.path.join(root,row['Camera'])))
                                                                                                 
def clip_videos(command):                                                            
    os.system(command)                                       
                                                                                
if DEBUG:
    print(camera_map)
    print(sync)
    print('\n'.join(commands))
else:
    pool = Pool(processes=MAX_PROCESSES)                                                        
    pool.map(clip_videos, commands) 
