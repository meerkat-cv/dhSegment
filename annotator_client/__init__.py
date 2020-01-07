import logging
import requests
import json
from pathlib import Path

import cv2
import urllib.request as urllib2
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class DatasetNotFoundError(Exception):
    """Exception raised when the dataset was not found"""

class MultipleDatasetFoundError(Exception):
    """Exception raised when multiple datasets were found with the same name"""

class PreAnnotator():

    def __init__(self, dataset_name, annotator_url = 'http://192.168.1.42:8094/annotator_supreme', create_if_new=False):
        self.dataset_name = dataset_name
        self.dataset_id = None
        self.url = annotator_url
        self.logger = logging.getLogger(__name__)

        retries = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retries)
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        if create_if_new :
            self.create_dataset()
        else:
            self.dataset_id = self.get_dataset_id()[0]


    def get_dataset_id(self):
        r = self.session.get(self.url+"/dataset/all")
        datasets = r.json()

        id_list = [ d['id'] for d in datasets['datasets'] if d['name'] == self.dataset_name ]
        if len(id_list) > 1:
            raise MultipleDatasetFoundError(
                    "Multiple datasets found for this name: "+str(id_list))

        if len(id_list) == 0:
            raise DatasetNotFoundError("Dataset not found: %s" % self.dataset_name)

        return id_list

    def get_dataset_annotations(self):
        if self.dataset_id is None:
            self.dataset_id = self.get_dataset_id()[0]

        r = self.session.get(self.url+'/annotation/'+str(self.dataset_id)+'/all')
        return r.json()

    def get_image_annotation(self, img_id):
        if self.dataset_id is None:
            self.dataset_id = self.get_dataset_id()[0]

        r = self.session.get(self.url+'/annotation/'+str(self.dataset_id)+'/'+str(img_id))
        return r.json()

    def create_dataset(self):
        try:
            if self.get_dataset_id() :
                print("Dataset with this name already exists!")
        except DatasetNotFoundError :
            data = { 'name' : self.dataset_name }
            r = self.session.post(self.url+"/dataset", json = data )

        self.dataset_id = self.get_dataset_id()[0]
        print("Using dataset with id: %s" % self.dataset_id )
        
    def upload_image(self,image_path):
        """ Returns the imageId in the response"""

        image_name = str(Path(image_path).name)
        files = { 'image': open(image_path, 'rb'), 'filename' :  image_name}
        r = self.session.post(self.url+"/annotation/%d"%self.dataset_id, files = files)

        return self.valid_response(r)

    def upload_image_url(self,image_url):
        """ Returns the imageId in the response"""

        payload = { 'imageUrl': image_url }
        r = self.session.post(self.url+"/annotation/%d"%self.dataset_id, json = payload)

        return self.valid_response(r)


    def add_dataset_ocr_field(self,ocr_field):
        payload = { 'ocr_field': ocr_field }
        r = self.session.post( self.url+"/dataset/%d/ocr_field" % self.dataset_id, json = payload )

    def valid_response(self, r):
        new_image=True
        if r.status_code == 432:
            print(r.json())
            try:
                img_id = r.json()['message']['image_id']
                new_image = False
            except TypeError as e:
                raise ValueError(r.json()['message'])
        else:
            img_id = r.json()['image_id']
        
        return img_id, new_image

    def update_image_annotation(self,image_id, annotation_json):
        r = self.session.patch(self.url+"/annotation/%d/%d" % ( self.dataset_id , image_id ) , json = annotation_json )
        print(r.text)

    def download_image_from_url(self, url, output_dir, output_name):
        """ Downloads the image from the annotator URL and saves on output_dir """
        req = urllib2.Request(self.url+'/'+url, headers={'User-Agent' : "Annotator-Supreme"})
        res = urllib2.urlopen(req)
        if res.getcode() != 200:
            raise Exception('Invalid status code '+str(res.getcode())+' from image url')
        data = res.read()
        with open(output_dir+'/'+output_name,'wb') as tim:
            tim.write(data)

