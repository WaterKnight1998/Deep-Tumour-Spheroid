from __future__ import absolute_import
from .predict import predict_image, predict_folder
from .gui import show_gui

import sys
import argparse

def main():
    parent_parser = argparse.ArgumentParser(description="Deep-TumourSpheroid is developed by David Lacalle Castillo")

    subparsers = parent_parser.add_subparsers(title='Subcommands',
                                              description='There are 3 supported commands: gui, image, folder',
                                              dest='mode',
                                              help='Additional help')

    # GUI Command
    parser_gui = subparsers.add_parser('gui', description='This GUI allows you to convert: ND2 to PNG, ROI to Mask and generate dataset applying the previous two transforms',
                                       help='Opens the GUI')

    # Image Command
    parser_image = subparsers.add_parser('image', description='The prediction is saved with same name as input follows by \'_pred\' thats why just output folder is passed',
                                         help='Predict on an image')
    parser_image.add_argument("input", help='File path (str)', type=str)
    parser_image.add_argument("output", help='Output folder path (str)', type=str) 

    # Folder Command
    parser_folder = subparsers.add_parser('folder', description='Predict on all the images of the input folder and stores result at the given folder',
                                          help='Predict on an all the images of the folder')
    parser_folder.add_argument("input", help='Input folder path (str)', type=str)
    parser_folder.add_argument("output", help='Output folder path (str)', type=str)

    # Parsing args
    args = parent_parser.parse_args()

    if args.mode == "gui":
        show_gui()
    elif args.mode == "image":
        print(args.input)
        print(args.output)
        predict_image(input_image_path=args.input, output_folder=args.output)
    elif args.mode == "folder":
        predict_folder(input_folder=args.input, output_folder=args.output)
    
    
