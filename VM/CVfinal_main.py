#!/usr/bin/env python
# coding: utf-8

# In[1]:


import asyncio
import io
import glob
import os
import sys
import time
import uuid
import requests
from urllib.parse import urlparse
from io import BytesIO
# To install this module, run:
# python -m pip install Pillow
from PIL import Image, ImageDraw
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person

from azure.storage.blob import BlobProperties
from azure.core.paging import ItemPaged
from typing import List

from azure.storage.blob import BlobServiceClient
# In[2]:

# This key will serve all examples in this document.
KEY = "Type your own key"

# This endpoint will be used in all examples in this quickstart.
ENDPOINT = "Type your own endpoint"

# Create an authenticated FaceClient.
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))


# In[3]:
blob_service_client = BlobServiceClient.from_connection_string(
    "Type your own connection string")
container_client = blob_service_client.get_container_client(
    "Type your own container name")  # for training
container_client_pi = blob_service_client.get_container_client(
    "Type your own container name")  # for rasPi (Image for detection )
container_client_con = blob_service_client.get_container_client(
    "Type your own container name")  # for confidence
# In[4]:


# generate GROUP ID
# Used in the Person Group Operations and Delete Person Group examples.
# You can call list_person_groups to print a list of preexisting PersonGroups.
# SOURCE_PERSON_GROUP_ID should be all lowercase and alphanumeric. For example, 'mygroupname' (dashes are OK).


PERSON_GROUP_ID = str(uuid.uuid4())  # assign a random ID (or name it anything)

# Used for the Delete Person Group example.
# assign a random ID (or name it anything)
TARGET_PERSON_GROUP_ID = str(uuid.uuid4())


'''
Create the PersonGroup
'''
# Create empty Person Group. Person Group ID must be lower case, alphanumeric, and/or with '-', '_'.
print('Person group:', PERSON_GROUP_ID)
face_client.person_group.create(
    person_group_id=PERSON_GROUP_ID, name=PERSON_GROUP_ID)


# In[5]:
class Folder:
    def __init__(self, name, file=[]):
        self.name = name
        self.file = file


def getFileNum(dir):
    fileList = []
    fileSize = 0
    folderCount = 0
    rootdir = os.getcwd() + dir

    for root, subFolders, files in os.walk(rootdir):
        folderCount += len(subFolders)
        for file in files:
            f = os.path.join(root, file)
            fileSize = fileSize + os.path.getsize(f)
            fileList.append(f)

    print("Total Size is {0} bytes".format(fileSize))
    print("Total Files", len(fileList))
    print("Total Folders", folderCount)
    return folderCount


def newFolder(folder_name):
    try:
        os.mkdir(os.getcwd() + folder_name)
    except:
        print('Folder existed: ', folder_name)


def index_of_list(a, Person_Name_List):
    index = -99
    for i in range(len(Person_Name_List)):
        if a == Person_Name_List[i]:
            index = i
    return index


newFolder("/allpeople/")  # for personal image training
newFolder("/pi/")  # for save detection image shoot from rasPi


while(1):
    # get all image in container (training)
    blobs_list = container_client.list_blobs()

    # check if container have image
    blob_paged: ItemPaged[BlobProperties] = container_client.list_blobs()
    blob_list: List[dict] = list(blob_paged)
    number_of_blobs: int = len(blob_list)

    # if container "testcontainer" have image
    if number_of_blobs > 0:

        for blob in blobs_list:
            print(blob.name + '\n')
            blob_client = container_client.get_blob_client(blob.name)

        DEST_FILE = ""
        PERSON_NAME = ""

        for i in range(len(blob.name)):
            if blob.name[i] == "-":
                j = i + 1
                while (j < len(blob.name)):
                    DEST_FILE = DEST_FILE + blob.name[j]
                    j = j + 1
                break
            PERSON_NAME = PERSON_NAME + blob.name[i]

        if (PERSON_NAME == 'train'):

            blob_client.delete_blob()
            file_NUM = getFileNum("/allpeople")  # numbers of people

            #########################################################################
            Person_Name_List = []
            Person_List = []
            Floder_List = []

            path = os.getcwd() + '/allpeople'

            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    a = os.path.join(dirpath).split("/")[-1].split("\\")[-1]

                    index = index_of_list(a, Person_Name_List)
                    if index == -99:
                        Person_Name_List.append(a)
                        Floder_List.append(Folder(a, []))
                        Floder_List[len(Floder_List)-1].file.append(filename)
                    else:
                        Floder_List[index].file.append(filename)

            ''' 
            #check saved images
            for i in range(len(Floder_List)) :
                print(Floder_List[i].name,end='')
                print(Floder_List[i].file)
            '''

            # Define all people
            for i in range(len(Person_Name_List)):
                tamp = face_client.person_group_person.create(
                    PERSON_GROUP_ID, Person_Name_List[i])
                Person_List.append(tamp)

            print(Person_List)

            #########################################################################
            '''
            Detect faces and register to correct person
            '''
            # Add to all person
            for i in range(len(Floder_List)):
                for image in Floder_List[i].file:
                    path = os.getcwd() + '/allpeople/' + \
                        Floder_List[i].name + "/"
                    w = open(path+image, 'r+b')
                    print(image)
                    try:
                        face_client.person_group_person.add_face_from_stream(
                            PERSON_GROUP_ID, Person_List[i].person_id, w)
                    except:
                        print("no face detect")

            #########################################################################
            '''
            Train PersonGroup
            '''
            print('Training the person group...')
            # Train the person group
            face_client.person_group.train(PERSON_GROUP_ID)

            while (True):
                training_status = face_client.person_group.get_training_status(
                    PERSON_GROUP_ID)
                print("Training status: {}.".format(training_status.status))
                print()
                if (training_status.status is TrainingStatusType.succeeded):
                    break
                elif (training_status.status is TrainingStatusType.failed):
                    sys.exit('Training the person group has failed.')
                time.sleep(1)
            #########################################################################

        elif(PERSON_NAME == 'undefined'):
            blob_client.delete_blob()

        else:

            print(PERSON_NAME)
            print(DEST_FILE)

            person_path = os.getcwd() + "/allpeople/" + PERSON_NAME

            try:
                os.mkdir(person_path)
            except:
                print('Personal folder exist')

            with open(person_path+"/" + DEST_FILE, "wb") as my_blob:
                download_stream = blob_client.download_blob()
                my_blob.write(download_stream.readall())
            # [END list_blobs_in_container]

            blob_client.delete_blob()

    blob_paged_pi: ItemPaged[BlobProperties] = container_client_pi.list_blobs()
    blob_list_pi: List[dict] = list(blob_paged_pi)
    number_of_blobs_pi: int = len(blob_list_pi)

    if number_of_blobs_pi > 0:
        for blob in blob_list_pi:
            print(blob.name + '\n')
            blob_client_pi = container_client_pi.get_blob_client(blob.name)

        person_path = os.getcwd() + "/pi"

        try:
            os.mkdir(person_path)
        except:
            print('folder existed')

        with open(person_path+"/" + blob.name, "wb") as my_blob:
            download_stream = blob_client_pi.download_blob()
            my_blob.write(download_stream.readall())
        # [END list_blobs_in_container]

        blob_client_pi.delete_blob()

        #########################################################################
        '''
        Identify a face against a defined PersonGroup
        '''
        # Group image for testing against
        person_path = os.getcwd() + "/pi/detection.jpg"
        test_image_array = glob.glob(person_path)
        image = open(test_image_array[0], 'r+b')

        """ if Azure face API use F0(free account) sleep 60s
        print('Pausing for 60 seconds to avoid triggering rate limit on free account...')
        time.sleep (60)
        """

        # Detect faces
        face_ids = []
        # We use detection model 2 because we are not retrieving attributes.
        faces = face_client.face.detect_with_stream(
            image, detectionModel='detection_02')
        for face in faces:
            face_ids.append(face.face_id)

        #########################################################################
        # Identify faces
        print(face_ids)
        try:
            results = face_client.face.identify(face_ids, PERSON_GROUP_ID)
            print('Identifying faces in {}'.format(
                os.path.basename(image.name)))
            if not results:
                print('No person identified in the person group for faces from {}.'.format(
                    os.path.basename(image.name)))
            for person in results:
                if len(person.candidates) > 0:
                    print('Person for face ID {} is identified in {} with a confidence of {}.'.format(
                        person.face_id, os.path.basename(image.name), person.candidates[0].confidence))  # Get topmost confidence score
                else:
                    print('No person identified for face ID {} in {}.'.format(
                        person.face_id, os.path.basename(image.name)))

                f = open('pi/'+str(person.candidates[0].confidence), 'w')
                f.close()
                blob_client_con = container_client_con.get_blob_client(
                    str(person.candidates[0].confidence))
                with open('pi/' + str(person.candidates[0].confidence), "rb") as data:
                    blob_client_con.upload_blob(data)

        except:
            print("shot again")
            f = open('pi/' + "-1", 'w')
            f.close()
            blob_client_con = container_client_con.get_blob_client("-1")
            with open('pi/' + "-1", "rb") as data:
                blob_client_con.upload_blob(data)