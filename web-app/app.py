# ML
import torchvision.transforms as transforms
import torch

# Web App
from flask import Flask, render_template, send_file, request, json
app = Flask(__name__)

# Show Images
from PIL import Image
from skimage import color
import io
import numpy as np
import base64

# Biomedical Images
from nd2reader import ND2Reader
from skimage import exposure, img_as_ubyte

# Temp file
from tempfile import NamedTemporaryFile

# List dir
import os

# Suppress all models warnings
import warnings
warnings.filterwarnings('ignore')

# ---------------------Models-----------------------------------
models = {}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 

mypath="/app/models/"
onlyfiles = [f.replace(".pth","") for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
onlyfiles.sort()


for model_name in onlyfiles:
    model = torch.jit.load("models/"+model_name+".pth")
    model = model.cpu()
    model.eval()

    models[model_name]=model


# ---------------------Best Model---------------------------------
best_model = ""
for model_name in onlyfiles:
    if "best" in model_name:
        best_model = model_name.replace("-best","")
        models[best_model] = models.pop(model_name)



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

u2net_name = "u^2-net"
maskrcnn_name = "mask-rcnn"

def inference(model_name, input):
    model=models[model_name]

    # Moving to GPU if available
    model = model.to(device)

    with torch.no_grad():
        if u2net_name in model_name.lower():
            outputs, _, _, _, _, _, _ = model(input)
        elif maskrcnn_name in model_name.lower():
            _,outputs = model([input[0]])
        else:
            outputs = model(input)

    if u2net_name in model_name.lower():
        outputs=torch.sigmoid(outputs)
        outputs=normPRED(outputs)
        outputs=outputs>0.5
        outputs=outputs.type(torch.uint8)
        outputs=outputs[0]
    elif maskrcnn_name in model_name.lower():
        outputs=outputs[0]
        outputs=outputs["masks"]
        if outputs.shape[0]>0:
            outputs=outputs[0]
            outputs=outputs>0.5
            outputs=outputs.type(torch.uint8)
    else:
        outputs = torch.argmax(outputs,1)

    # Moving to CPU
    model = model.cpu()
    
    return outputs

def mask_into_image(image, mask):
    mask = mask*255

    prediction = Image.fromarray(np.uint8(mask[0]),"L")

    # Save Mask to buffer
    buff = io.BytesIO()
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
    out_img.save(buff, "PNG")

    return buff

def get_prediction_several_models(file, model_names):
    img_bytes = file.read()
    
    image = None
    if file.filename.endswith(".nd2"):
        # Named Temporal File in RAM dir="/dev/shm" does the trick
        tmp_file=NamedTemporaryFile(delete=False, suffix=".nd2", dir="/dev/shm")
        tmp_file.write(img_bytes)
        tmp_file.close()
        with ND2Reader(tmp_file.name) as image_reader:
            nd2Image = image_reader[0]

            # Image Conversion --------------------------------------

            # Transforming image from 16bits into 8 bit
            nd2Image = img_as_ubyte(nd2Image)

            # Reescaling color intensity, if not image gets very dark
            nd2Image = exposure.rescale_intensity(nd2Image)

            # Converting 1 channel image to 3 channels
            nd2Image = color.grey2rgb(nd2Image)
            image = Image.fromarray(nd2Image)

        # Removing Temporal File
        os.unlink(tmp_file.name)
    else:
        img_bytes = io.BytesIO(img_bytes)
        image = Image.open(img_bytes)

    # We need to make it before    
    image = transforms.Resize((1002,1002))(image)    

    tensor = transform_image(image=image)

    data = {}
    data["filename"]=file.filename
    buff = io.BytesIO()
    image.save(buff, "PNG")
    data["image"]= base64.encodebytes(buff.getvalue()).decode('ascii')
    data["mask"] = []

    masks = []
    for model_name in model_names:
        mask = inference(model_name=model_name, input=tensor)
        mask_ndarray = mask.detach().cpu().numpy()
        # Releasing CUDA Memory
        del mask
        masks.append(mask_ndarray)

        buff = mask_into_image(image=image, mask=mask_ndarray)

        aux_model={}
        aux_model["model_name"]=model_name + " Prediction "
        aux_model["mask_data"]=base64.encodebytes(buff.getvalue()).decode('ascii')

        data["mask"].append(aux_model)
    
    # If more than one prediction do ensemble
    if len(masks)>1:
        # Convert int mask to bool
        for i in range(len(masks)):
            masks[i] = masks[i].astype(bool)

        # And & OR Ensemble
        and_mask=masks[0]
        or_mask=masks[0]

        for i in range(1,len(masks)):
            and_mask=np.logical_and(and_mask,masks[i])
            or_mask=np.logical_or(or_mask,masks[i])

        and_mask=and_mask.astype(int)
        or_mask=or_mask.astype(int)

        # And Ensemble
        buff = mask_into_image(image=image, mask=and_mask)

        aux_and={}
        aux_and["model_name"]="Ensemble AND"
        aux_and["mask_data"]=base64.encodebytes(buff.getvalue()).decode('ascii')
        data["mask"].append(aux_and)

        # OR Ensemble
        buff = mask_into_image(image=image, mask=or_mask)

        aux_or={}
        aux_or["model_name"]="Ensemble OR"
        aux_or["mask_data"]=base64.encodebytes(buff.getvalue()).decode('ascii')
        data["mask"].append(aux_or)
        
    return data

# /

@app.route("/",methods=["GET"])
def main():
    return render_template("index.html")

alpha = 0.8
@app.route("/",methods=["POST"])
def best_model_inference():
    if request.method == "POST":
        files = request.files.getlist("file")

        res = []
        for file in files:
            data = get_prediction_several_models(file, [best_model])
            res.append(data)
        
        response = app.response_class(
            response=json.dumps(res),
            status=200,
            mimetype='application/json'
        )
    return response

# /chooseModel

@app.route("/chooseModel",methods=["GET"])
def get_chooseModel_view():
    model_names = list(models.keys())
    return render_template("chooseModel.html",model_names=model_names)

@app.route("/chooseModel",methods=["POST"])
def chooseModel_inference():
    if request.method == "POST":
        files = request.files.getlist("file")

        model_name = request.form["model"]
        res = []
        for file in files:
            data = get_prediction_several_models(file, [model_name])
            res.append(data)
        
        response = app.response_class(
            response=json.dumps(res),
            status=200,
            mimetype='application/json'
        )
    return response

# /modelComparison

@app.route("/modelComparison",methods=["GET"])
def get_modelComparison_view():
    model_names = list(models.keys())
    return render_template("modelComparison.html",model_names=model_names)

@app.route("/modelComparison",methods=["POST"])
def modelComparison_inference():
    if request.method == "POST":
        files = request.files.getlist("file")

        model_names = request.form.getlist("models")
        res = []
        for file in files:
            data = get_prediction_several_models(file,model_names)
            res.append(data)
        
        response = app.response_class(
            response=json.dumps(res),
            status=200,
            mimetype='application/json'
        )
    return response

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
