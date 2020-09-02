from __future__ import absolute_import

# Read .nd2
import pims_nd2

# Files util
import os
from pathlib import Path
import shutil

# Image processing
import cv2
import numpy as np
from skimage import exposure, draw, io, img_as_ubyte, color

# ROI
from read_roi import read_roi_file, read_roi_zip

import sys

# Saving annotation
import json
import torch

# For test
import random


def nd2_converter(input_image_path, output_dir, output_type="png"):
    '''
    Converts ND2 image into a JPG or PNG.

    Parameters:
        input_image_path (str): Full path to the input file .nd2
        output_dir (str): path of the directory where you would like to save the result
        output_type (str): "jpg" or "png"
    '''

    # Reading .nd2 image
    nd2_image = pims_nd2.ND2_Reader(input_image_path)[0]

    # Image Conversion --------------------------------------

    # Transforming image from 16bits into 8 bit
    nd2_image = img_as_ubyte(nd2_image)
    # nd2_image = color.gray2rgb(nd2_image)

    # Reescaling color intensity, if not image gets very dark
    nd2_image = exposure.rescale_intensity(nd2_image)
    #nd2_image = color.grey2rgb(nd2_image)
    
    # Saving result
    io.imsave(os.path.join(output_dir, Path(
        input_image_path).stem+"."+output_type), nd2_image)


def tiff_converter(input_image_path, output_dir, output_type="png"):
    '''
    Converts tiff image into a JPG or PNG.

    Parameters:
        input_image_path (str): Full path to the input file .tiff or .tif
        output_dir (str): path of the directory where you would like to save the result
        output_type (str): "jpg" or "png"
    '''

    # Reading image
    tiff_image = io.imread(input_image_path)

    # Image Conversion --------------------------------------

    # Transforming image from 16bits into 8 bit
    tiff_image = img_as_ubyte(tiff_image)
    # image = color.gray2rgb(image)

    # Reescaling color intensity, if not image gets very dark
    tiff_image = exposure.rescale_intensity(tiff_image)

    # Saving result
    io.imsave(os.path.join(output_dir, Path(
        input_image_path).stem+"."+output_type), tiff_image)


def roi_to_mask(input_roi_file, output_dir, output_type="png"):
    '''
    Converts the Mask into a JPG or PNG.

    Parameters:
        input_image_path (str): Full path to the input mask .roi or the zip containing the .roi
        output_dir (str): path of the directory where you would like to save the result
        output_type (str): "jpg" or "png"
    '''

    roi_name = os.path.basename(input_roi_file).replace(".roi", "")
    print("Ruta: {} Imagen: {}".format(input_roi_file, roi_name))
    roi = []

    if input_roi_file.endswith(".roi"):
        roi = read_roi_file(input_roi_file)
        # Extracting raw data from dictionary
        roi = roi[roi_name]
    elif input_roi_file.endswith(".zip"):
        roi = read_roi_zip(input_roi_file)
        # Extracting raw data from dictionary
        roi = roi[list(roi.keys())[0]]

    # Creating 2D Matrix by concatenating X and Y axis ([y|x]).
    roi = np.column_stack((roi["y"], roi["x"]))
    image_name = ""
    if input_roi_file.endswith(".roi"):
        image_name = input_roi_file.replace(".roi", "."+output_type)
    elif input_roi_file.endswith(".zip"):
        image_name = input_roi_file.replace(".zip", "."+output_type)

    # Testing if image where the mask was extracted exists
    if Path(image_name).exists():
        imagen = io.imread(image_name)
        print("Shape: {}".format(imagen.shape))

        # Transfroming bounding polygon into mask
        mask = draw.polygon2mask(imagen.shape, roi)

        mask_name = image_name.replace("."+output_type, "")
        mask_name += "-Mask."+output_type

        # Transforming boolean matrix into a binary one (white color represents the selection and black colore represents the opposite)
        # Saving the mask into file
        cv2.imwrite(os.path.join(output_dir, Path(mask_name).stem +
                                 "."+output_type), (mask * 255)//255)


def generate_dataset(input_dir, output_dir, output_type="png", progress=None):
    '''
    Generates a Dataset in the output_dir from the data in input_dir.

    Parameters:
        input_dir (str): Full path to the directory which contains input data
        output_dir (str): path of the directory where you would like to save the result
        output_type (str): "jpg" or "png"
        progress: None or QProgressBar. In case of being QProgressBar is used for displaying the progress of the process
    '''

    if progress is not None:
        progress.setValue(50)

    p = Path(output_dir)
    if not p.exists():
        os.mkdir(p)

    # Converting ND2 and tiff into PNG
    for current_path, folders, files in os.walk(input_dir):
        for file in files:
            file_aux = os.path.join(current_path, file)
            # file_auxDst = file_aux.replace(input_dir, output_dir)
            # os.makedirs(os.path.dirname(file_auxDst), exist_ok=True)

            if file.endswith(".nd2"):
                if not os.path.exists(os.path.join(current_path, file.replace(".nd2", ".png"))):
                    nd2_converter(file_aux, current_path, output_type)
            elif file.endswith(".tiff") or file.endswith(".tif"):
                extension = file.split(".")[-1]
                if not os.path.exists(os.path.join(current_path, file.replace("."+extension, ".png"))):
                    tiff_converter(file_aux, current_path, output_type)
    if progress is not None:
        progress.setValue(50)
    # Transforming ROI into Mask
    for current_path, folders, files in os.walk(input_dir):
        for file in files:
            file_aux = os.path.join(current_path, file)
            if file.endswith(".roi") or file.endswith(".zip"):
                if not os.path.exists(os.path.join(current_path, Path(file).stem+"-Mask.png")):
                    roi_to_mask(file_aux, current_path, output_type)
    if progress is not None:
        progress.setValue(75)

    generate_training_data(input_dir, output_dir, output_type)

    if progress is not None:
        progress.setValue(100)

def generate_training_data(input_dir, output_dir, output_type="png"):
    output_dir_images = os.path.join(output_dir, "Images")
    output_dir_labels = os.path.join(output_dir, "Labels")

    os.makedirs(output_dir_images, exist_ok=True)
    os.makedirs(output_dir_labels, exist_ok=True)

    mask_filename_ending = "-Mask."+output_type
    image_filename_ending = "."+output_type
    
    i = 1
    for current_path, folders, files in os.walk(input_dir):
        for file in files:
            file_aux = os.path.join(current_path, file)
            if file.endswith(mask_filename_ending) and os.path.exists(file_aux.replace(mask_filename_ending, image_filename_ending)):
                shutil.copy2(file_aux, os.path.join(
                    output_dir_labels, "{}.{}".format(i, output_type)))
                shutil.copy2(file_aux.replace(mask_filename_ending, image_filename_ending), os.path.join(
                    output_dir_images, "{}.{}".format(i, output_type)))
                i += 1

def generate_test_set(input_dir, dataset_name, output_dir, output_type="png", p_split=0.25):
    output_dir_images = os.path.join(output_dir, "Images")
    output_dir_labels = os.path.join(output_dir, "Labels")

    os.makedirs(output_dir_images, exist_ok=True)
    os.makedirs(output_dir_labels, exist_ok=True)

    deleted_elems = []

    mask_ending = "-Mask."+output_type
    file_ending = "."+output_type

    i=1
    for current_path, folders, files in os.walk(input_dir):
        list_maks=[]
        for file in files:
            file_aux=os.path.join(current_path, file)
            if file_aux.endswith(mask_ending):
                list_maks.append(file_aux)
        num_elemns_total = len(list_maks)
        num_elemns_test = int(round(len(list_maks)*p_split))
        random.shuffle(list_maks)
        print("Path {} with {} total files using {} for test".format(current_path,num_elemns_total,num_elemns_test))
        
        elems_test = random.sample(list_maks,k=num_elemns_test)
        #print(elems_test)

        if len(elems_test)>0:
            for elem in elems_test:
                if os.path.exists(elem.replace(mask_ending, file_ending)):
                    deleted_elems.append(elem)

                    shutil.copy2(elem, os.path.join(
                            output_dir_labels, "{}.{}".format(i, output_type)))
                    os.remove(elem)

                    shutil.copy2(elem.replace(mask_ending, file_ending), os.path.join(
                            output_dir_images, "{}.{}".format(i, output_type)))
                    os.remove(elem.replace(mask_ending, file_ending))
                i += 1

    with open(os.path.join(output_dir,"deletedFiles.txt"),"w") as f:
        json.dump(deleted_elems,f,indent=4)


    dataset_realname = dataset_name.split(os.sep)[0]
    
    # It delete the same files in Manual Dataset
    deleted_elems_1 = deleted_elems.copy()
    for i in range(0,len(deleted_elems_1),1):
        deleted_elems_1[i] = deleted_elems_1[i].replace(dataset_realname,"manual")

    delete_files_in_folder(deleted_elems_1,output_type)

    # It delete the same files in Manual+EsferoidesJ Dataset
    deleted_elems_2 = deleted_elems.copy()
    for i in range(0,len(deleted_elems_2),1):
        deleted_elems_2[i] = deleted_elems_2[i].replace(dataset_realname,"manual + EsferoidesJ")
    delete_files_in_folder(deleted_elems_2,output_type)


def delete_files_in_folder(mask_files_list,output_type):
    '''
    From a list of mask file names it removes that elements and its associated image.

    Parameters:
        listFiles [str]: List of mask file names that contains the full path to that element
        output_type (str): "jpg" or "png"
    '''
    for mask_elem in mask_files_list:
        if os.path.exists(mask_elem):
            os.remove(mask_elem)
        image = mask_elem.replace("-Mask."+output_type,"."+output_type)
        if os.path.exists(image):
            os.remove(image)