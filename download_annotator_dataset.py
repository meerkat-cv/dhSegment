import os
import json
import logging
import shutil
import urllib.request 

import requests

def get_id_from_datasetname(dataset_name, annotator_url):
    res = requests.get(annotator_url+'/dataset/all')
    datasets = res.json()['datasets']
    sel_dataset = next((item for item in datasets if item["name"] == dataset_name), None)
    if sel_dataset is None:
        raise Exception("Dataset not found")
    return sel_dataset["id"]



def download_annotator_dataset(dataset_name = 'test_cheques', 
                annotator_url = 'http://monolito:8095/annotator_supreme/', 
                dataset_dir = 'datasets/'):
    
    dataset_id = get_id_from_datasetname(dataset_name, annotator_url)
    r = requests.get(annotator_url + '/annotation/' + str(dataset_id) + '/all')

    dataset_dir = dataset_dir + '/' + dataset_name
    if os.path.isdir(dataset_dir):
        logging.warning("dataset folder already exists, overwriting")
        shutil.rmtree(dataset_dir)
        
    os.mkdir(dataset_dir)
    
    annotations = r.json()
    with open(dataset_dir + '/anno.json', 'w') as f:
        json.dump(r.json(), f)
        print("Saving annotations")
    
    print("Downloading images...")
    for i,an in enumerate(annotations["annotations"]):
        file_url = annotator_url + '/' + an["image_url"]
        urllib.request.urlretrieve(file_url, dataset_dir + "/" + str(an["id"]) + ".png")
        print("\r{0}/{1} - Downloading {2}".format(i+1, len(annotations["annotations"]), file_url), end="")
    print("done")
        

if __name__ == "__main__":
    download_annotator_dataset(dataset_name="cnh_scanned",
                                 annotator_url='http://monolito:8094/annotator_supreme/',
                                 dataset_dir='datasets/')
# http://192.168.1.42:8095/annotator_supreme/dataset/all
