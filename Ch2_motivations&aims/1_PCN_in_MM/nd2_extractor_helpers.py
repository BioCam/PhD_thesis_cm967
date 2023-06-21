# ND2 Extractor helper script
# author: Georgeos Hardo

import matplotlib.pyplot as plt
import pprint
from pims import ND2Reader_SDK
pp = pprint.PrettyPrinter(indent=0)
from tabulate import tabulate
from tqdm.notebook import tqdm 
import cv2
from cowpy import cow
from celluloid import Camera
import colorama
from termcolor import colored
from joblib import Parallel, delayed, parallel_backend

def greeting():
    cheese = cow.Turtle()
    msg = cheese.milk("BakshiLab FAST ND2 Extractor - By Georgeos Hardo")
    print(msg)

def predict_t(directory): 
    frames =  ND2Reader_SDK(directory)
    frames.default_coords["t"] = 0
    t = 0
    while True:
        try:
            frames[t]
            t = t+1
        except:
            break
    frames.close()
    return int(t)

def predict_FOVs(directory):
    frames =  ND2Reader_SDK(directory)
    i = 1
    frames.default_coords["m"] = 0
    x_um = [frames[0].metadata["x_um"]]
    y_um = [frames[0].metadata["y_um"]]
    frames.default_coords["m"] = i
    while (x_um[0] != frames[0].metadata["x_um"] or y_um[0] != frames[0].metadata["y_um"]):
        frames.default_coords["m"] = i
        x_um.append(frames[0].metadata["x_um"])
        y_um.append(frames[0].metadata["y_um"])
        i+=1
    frames.close()
    return int(len(x_um) - 1)


def save_image(frame, i, img_format,save_directory,FOV,IMG_CHANNELS,channel):
    if (img_format == "TIF") or (img_format == "TIFF"):
        cv2.imwrite(save_directory + 'xy{}_T{}_{}.tif'.format(str(FOV).zfill(3),str(i).zfill(4),IMG_CHANNELS[channel]), frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
    if img_format == "PNG":
        cv2.imwrite(save_directory + 'xy{}_T{}_{}.png'.format(str(FOV).zfill(3),str(i).zfill(4),IMG_CHANNELS[channel]), frame)
    else:
        cv2.imwrite(save_directory + 'xy{}_T{}_{}.tif'.format(str(FOV).zfill(3),str(i).zfill(4),IMG_CHANNELS[channel]), frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1])

        
        
def main_loop(directory,save_directory):
    if save_directory[-1] != "/":
        save_directory = save_directory + "/"
    # Get parameters of the experiment
    frames =  ND2Reader_SDK(directory)
    IMG_HEIGHT = frames.metadata["tile_height"]
    IMG_WIDTH = frames.metadata["tile_width"]
    IMG_CHANNELS_COUNT = frames.metadata["plane_count"]
    SEQUENCES = frames.metadata["sequence_count"]
    IMG_CHANNELS = []
    for x in tqdm(range(IMG_CHANNELS_COUNT), desc = "Getting experiment info - please wait"):
        IMG_CHANNELS.append(frames.metadata["plane_{}".format(x)]["name"])
    frames.close() 
    num_FOVs = predict_FOVs(directory)
    print(colored("I predict that there are {} FOVs in the experiment, is this correct? (y/n) ".format(num_FOVs), 'red', attrs=['bold']))
    predict_correct = input()
    if predict_correct == "y":
        pass
    elif predict_correct == "n":
        num_FOVs = int(input("Enter the correct number of FOVs"))
    print(colored("Do you want to predict the number of timepoints automatically? (y/n) ".format(num_FOVs), 'red', attrs=['bold']))
    answer = input()
    if answer == "n":
        print("input number of timepoints")
        num_t = input()
        num_t = int(num_t)
    else:
        print(colored("Predicting number of timepoints in experiment. Please wait", "red", attrs=["bold"]))
        num_t = predict_t(directory)
        print(colored("I predict that there are {} timepoints in the experiment, is this correct? (y/n) ".format(num_t), 'red', attrs=['bold']))

    predict_correct = input()
    if predict_correct == "y":
        pass
    elif predict_correct == "n":
        num_t = int(input("Enter the correct number of FOVs"))

    assert int(SEQUENCES / num_FOVs) == num_t, "FOVs ({}) and timepoints ({}) do not match sequences ({}) in the experiment - check your inputs".format(num_FOVs,num_t,SEQUENCES)
    print(colored("Experiment parameters (please verify before proceeding with extraction".format(num_FOVs), 'blue', attrs=['bold']))
    print(tabulate([
        ['TIMEPOINTS', num_t],
        ['FOVs', num_FOVs],
        ['IMG_HEIGHT', IMG_HEIGHT], 
        ['IMG_WIDTH', IMG_WIDTH],
        ["IMG_CHANNELS_COUNT", IMG_CHANNELS_COUNT],
        ['IMG_CHANNELS', IMG_CHANNELS]], headers=['Parameter', 'Value'], tablefmt='orgtbl'))



    print(colored("Choose image format: (TIFF/PNG) ", 'red', attrs=['bold']))

    img_format = input()


    FOVs_list = list(range(num_FOVs))
    CHANNELS_list = list(range(IMG_CHANNELS_COUNT))
    
    if img_format == "PNG":
        joblib_workers = -1
    else:
        joblib_workers = 500

    with ND2Reader_SDK(directory) as frames:
        for FOV in tqdm(FOVs_list, desc = "Overall (FOV) progress"):
            for channel in tqdm(CHANNELS_list, desc = "Channel progress in FOV {}".format(FOV), leave = False):
                frames.iter_axes = 't'
                try:
                    frames.default_coords['c'] = channel
                except:
                    pass
                frames.default_coords['m'] = FOV
                Parallel(prefer="threads", n_jobs = joblib_workers)(delayed(save_image)(frames[i], i, img_format,save_directory,FOV,IMG_CHANNELS,channel) for i in tqdm(range(num_t), desc = "Frame progress in channel {}".format(IMG_CHANNELS[channel]), leave = False) )

 