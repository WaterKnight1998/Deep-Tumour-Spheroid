from __future__ import absolute_import

# ML
import torchvision.transforms as transforms
import torch

# Show Images
from PIL import Image
from skimage import color
import io
import numpy as np

# Biomedical Images
from nd2reader import ND2Reader
from skimage import exposure, img_as_ubyte

# List dir
import os
from pathlib import Path

# Suppress all models warnings
import warnings
warnings.filterwarnings("ignore")

# Download model
from tqdm import tqdm
import urllib.request

def normPRED(d):
    ma = torch.max(d)
    mi = torch.min(d)

    dn = (d-mi)/(ma-mi)

    return dn


def transform_image(image):
    my_transforms = transforms.Compose([transforms.ToTensor(),
                                        transforms.Normalize(
                                            [0.485, 0.456, 0.406],
                                            [0.229, 0.224, 0.225])])
    image_aux = image
    return my_transforms(image_aux).unsqueeze(0).to(device)


def inference(model_name, input):
    model=models[model_name]

    # Moving to GPU if available
    model = model.to(device)

    with torch.no_grad():
        outputs = model(input)

    outputs = torch.argmax(outputs,1)

    # Moving to CPU
    model = model.cpu()
    
    return outputs


def save_mask_prediction(image, mask, width, height, output_path, 
                         name, alpha=0.8, output_extension = "png"):
    mask = mask*255

    prediction = Image.fromarray(np.uint8(mask[0]),"L")

    image = np.array(image)
    output = color.grey2rgb(np.array(prediction))

    # Selecting color of tumor
    output[np.where((output==[255,255,255]).all(axis=2))] = [0,0,255]

    # Changing background to white
    output[np.where((output==[0,0,0]).all(axis=2))] = [255,255,255]

    # Blending image with it's mask
    out_img = np.zeros(image.shape, dtype=image.dtype)
    out_img[:,:,:] = (alpha * image[:,:,:]) + ((1-alpha) * output[:,:,:])
    out_img = Image.fromarray(out_img)

    # Save Blend
    out_img = transforms.Resize((height,width))(out_img)
    extension = name.split(".")[-1]
    out_img.save(output_path+name.replace("."+extension, "_blend."+output_extension))

    # Save Mask
    out_mask = transforms.Resize((height,width))(prediction)
    out_mask.save(output_path+name.replace("."+extension, "_pred."+output_extension))




def get_prediction_several_models(input_path, output_path, model_names):
    if input_path.endswith(".nd2"):
        
        with ND2Reader(input_path) as image_reader:
            nd2Image = image_reader[0]

            # Image Conversion --------------------------------------

            # Transforming image from 16bits into 8 bit
            nd2Image = img_as_ubyte(nd2Image)

            # Reescaling color intensity, if not image gets very dark
            nd2Image = exposure.rescale_intensity(nd2Image)

            # Converting 1 channel image to 3 channels
            nd2Image = color.grey2rgb(nd2Image)
            image = Image.fromarray(nd2Image)
    else:
        
        image = Image.open(input_path)
        image_np = np.array(image)

        # Convert to 3 Channels if not
        if image_np.shape[0] != 3:
            if input_path.lower().endswith(".tiff") or input_path.lower().endswith(".tif"):
                image_np = exposure.rescale_intensity(image_np)
            image_np = color.grey2rgb(image_np)
            image = Image.fromarray(image_np)

    width, height = image.size

    image = transforms.Resize((1002,1002))(image)
    tensor = transform_image(image=image)

    for model_name in model_names:
        mask = inference(model_name=model_name, input=tensor)
        mask_ndarray = mask.detach().cpu().numpy()

        name = input_path.split(os.sep)[-1]

        if name.count("/")>0:
            name = name.split("/")[-1]
        elif name.count("")>0:
            name = name.split("\\")[-1]

        save_mask_prediction(image=image, mask=mask_ndarray, width=width, height=height,
                                     output_path=output_path,
                                     name=name)


#------------Download weights--------------------------------------
hrnet_model_name = "HRNet Seg"

hrnet_weights = str(Path.home())+f"{os.sep}.deep-tumour-spheroid{os.sep}models{os.sep}"+ hrnet_model_name + ".pth"

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

url = "https://dl.dropboxusercontent.com/s/b7ssl9a3wxezahx/HRNet%20Seg.pth?dl=0"
if  not os.path.exists(hrnet_weights):
    with DownloadProgressBar(unit="B", unit_scale=True,
                             miniters=1, desc=url.split("/")[-1]) as t:
        os.makedirs(os.path.dirname(hrnet_weights), exist_ok=True)
        urllib.request.urlretrieve(url, filename=hrnet_weights, reporthook=t.update_to)


# ---------------------Models-----------------------------------
models = {}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 

# HRNet

model = torch.jit.load(hrnet_weights)
model = model.cpu()
model.eval()

models[hrnet_model_name]=model


def predict_image(input_image_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    get_prediction_several_models(input_image_path, output_folder, [hrnet_model_name])


def predict_folder(input_folder, output_folder):
    os.makedirs(output_folder,exist_ok=True)
    images_path = []
    for image_path in os.listdir(input_folder):
        if image_path.lower().split(".")[-1] in ["jpg", "png", "nd2", "tif", "tiff"]:
            images_path.append(input_folder+image_path)
    for image_path in images_path:    
        if "_pred." not in image_path.lower():
            get_prediction_several_models(image_path, output_folder, [hrnet_model_name])