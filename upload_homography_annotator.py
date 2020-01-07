import os
import json

import requests

from annotator_client import PreAnnotator

def get_emmett_response(emmett_url, image_path, app_key = None):
    header = {'app_key': app_key} if app_key else {}
    res = requests.post(emmett_url + "documents/br/cnh/read",
                        files={'image': open(image_path, 'rb')},
                        headers=header)
    return res.json()



def upload_homography_annotator(folderpath, emmett_url, annotator_url, dataset_name):
    """
    This function gets all images in a folder, use Emmett to
    find the homography and upload to annotator in order to be
    revised
    """

    filelist = [file for file in os.listdir(
        folderpath) if file.endswith('.png') or file.endswith('.jpg') or file.endswith('.jpeg')]
    
    dataset = PreAnnotator(
                dataset_name, annotator_url=annotator_url, create_if_new=True)
    for fn in filelist:
        image_filepath = folderpath+"/"+fn
        print(image_filepath)
        res = get_emmett_response(emmett_url, image_filepath)
        # [{'document': {'type': 'cnh_front', 'corners': [{'x': 871.936, 'y': 95.68},
        if "documents" not in res or len(res["documents"]) == 0:
            print("WARNING: DID NOT FOUND DOCUMENT")
        elif len(res["documents"]) > 1:
            print("WARNING: TOO MANY DOCS, SKIPPING")
        else:
            corners = res["documents"][0]["document"]["corners"]
            

            img_id, is_new = dataset.upload_image(image_filepath)

            payload = {"landmarks": [
                            {
                                "label": "",
                                "points": corners
                            }
                        ]}

            dataset.update_image_annotation(img_id, payload)
            print("\nCool! Done!\n")

            
upload_homography_annotator("/Users/gustavofuhr/meerkat/datasets/cnhs/front",
                            "http://monolito:40020/emmett/",
                            "http://localhost:8094/annotator_supreme",
                            "front_cnh_homo")

upload_homography_annotator("/Users/gustavofuhr/meerkat/datasets/cnhs/back",
                            "http://monolito:40020/emmett/",
                            "http://localhost:8094/annotator_supreme",
                            "back_cnh_homo")
