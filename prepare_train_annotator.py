import os
import json
import shutil

import cv2
import numpy as np

from download_annotator_dataset import download_annotator_dataset
from distinguishable_colors import bgr_colors, rgb_colors


def draw_filled_poly(image, landmarks, poly_color):
    scale_f = 1.0
    pts = []
    pts.append([landmarks["points"][0]["x"]*scale_f,
                landmarks["points"][0]["y"]*scale_f])
    pts.append([landmarks["points"][1]["x"]*scale_f,
                landmarks["points"][1]["y"]*scale_f])
    pts.append([landmarks["points"][2]["x"]*scale_f,
                landmarks["points"][2]["y"]*scale_f])
    pts.append([landmarks["points"][3]["x"]*scale_f,
                landmarks["points"][3]["y"]*scale_f])
    pts = np.array(pts)
    cv2.fillPoly(image, np.int32([pts]), color=poly_color)


def create_base_folders(train_foldername):
    os.mkdir(train_foldername)
    os.mkdir(train_foldername+"/train")
    os.mkdir(train_foldername+"/train/images")
    os.mkdir(train_foldername+"/train/labels")
    os.mkdir(train_foldername+"/eval")
    os.mkdir(train_foldername+"/eval/images")
    os.mkdir(train_foldername+"/eval/labels")
    os.mkdir(train_foldername+"/output_model")

def make_config_dict(train_foldername):
    config_dict = {
        "training_params": {
            "learning_rate": 5e-5,
            "batch_size": 1,
            "make_patches": False,
            "training_margin": 0,
            "n_epochs": 30,
            "data_augmentation": True,
            "data_augmentation_max_rotation": 0.2,
            "data_augmentation_max_scaling": 0.2,
            "data_augmentation_flip_lr": True,
            "data_augmentation_flip_ud": True,
            "data_augmentation_color": False,
            "evaluate_every_epoch": 10
        },
        "pretrained_model_name": "resnet50",
        "prediction_type": "CLASSIFICATION",
        "train_data": "{0}/train".format(train_foldername),
        "eval_data": "{0}/eval".format(train_foldername),
        "classes_file": "{0}/classes.txt".format(train_foldername),
        "model_output_dir": "{0}/output_model".format(train_foldername),
        "gpu": "0"
    }

    return config_dict

def prepare_train_annotator(annotator_url, 
                            dataset_name, 
                            train_foldername = "train_data", 
                            eval_percentage=0.1, 
                            redownload_dataset = False):
    if not os.path.isdir("datasets/" + dataset_name) or redownload_dataset:
        download_annotator_dataset(dataset_name, annotator_url)

    if os.path.isdir(train_foldername):
        print("Removing {0}... It's gone!".format(train_foldername))
        shutil.rmtree(train_foldername)

    create_base_folders(train_foldername)
    
    with open("datasets/" + dataset_name + "/anno.json") as f:
        all_annotations = json.load(f)
        max_classes = -1

        for anno in all_annotations["annotations"]:
            if len(anno["landmarks"]) > 0:
                print("Using image:", anno["id"] )
                image = cv2.imread("datasets/{0}/{1}.png".format(dataset_name, anno["id"]))
                label = np.zeros((image.shape[0], image.shape[1], image.shape[2]), dtype=np.uint8)

                for ith,land in enumerate(anno["landmarks"]):
                    if len(land["points"]) == 4:
                        draw_filled_poly(label, land, bgr_colors[ith])
                        if ith+1 > max_classes:
                            max_classes = ith+1
                    else:
                        print("Skipping landmark not quadrilateral")

                # cv2.imshow("image", image)
                # cv2.imshow("label", label)
                # cv2.waitKey(0)

                foldern = "train"
                if np.random.uniform() < eval_percentage:
                    foldern = "eval"
                cv2.imwrite(
                    "{0}/{1}/images/image_{2:05d}.png".format(train_foldername, foldern, anno["id"]), image)
                cv2.imwrite(
                    "{0}/{1}/labels/image_{2:05d}.png".format(train_foldername, foldern, anno["id"]), label)

            else: 
                print("Skipping:", anno["id"] )

        with open(train_foldername+"/classes.txt", 'w') as c_fid:
            c_fid.write("0 0 0\n")
            for c in rgb_colors[:max_classes]:
                c_fid.write("{0} {1} {2}\n".format(*c))

        cfg = make_config_dict(train_foldername)
        with open(train_foldername+"/confid.json", 'w') as c_fid:
            json.dump(cfg, c_fid, indent=4, sort_keys=True)
 
    print("Done.")
        


if __name__ == "__main__":
    prepare_train_annotator(
        "http://localhost:8094/annotator_supreme/", "cnh_norm_test", train_foldername = "cnh_field_train", redownload_dataset=True)

