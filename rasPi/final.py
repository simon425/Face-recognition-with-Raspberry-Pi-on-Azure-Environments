import RPi.GPIO as GPIO
import picamera
import time
from azure.storage.blob import BlobServiceClient

from azure.storage.blob import BlobProperties
from azure.core.paging import ItemPaged
from typing import List

connection_string = "type your own storage account connection_string"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

picontainer = "type your own container name (for upload detection imaeges)"
confidence = "type your own container name (for get confidence)"
container_client = blob_service_client.get_container_client(picontainer)
container_client_detect = blob_service_client.get_container_client(confidence)

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(23, GPIO.IN)

i = 0

camera = picamera.PiCamera()

GPIO.output(17, False)
GPIO.output(18, False)
print("Press Button!!")

while True:
    confidence = 0.0
    input = GPIO.input(23)
    if input == 1:
        i += 1
        print("Button pressed (" + str(i) + ")")

        camera.capture("detection.jpg")

        print("Wait for image upload~~")

        blob_client = container_client.get_blob_client("detection.jpg")
        with open("detection.jpg", "rb") as data:
            blob_client.upload_blob(data)

        print("Upload success!!")

        blobs_list_detect = container_client_detect.list_blobs()
        while (1):

            # check is any image exist in container

            blob_paged_detect = ItemPaged[BlobProperties]
            blob_paged_detect = container_client_detect.list_blobs()

            blob_list_detect = List[dict]
            blob_list_detect = list(blob_paged_detect)

            number_of_blobs_detect = int(len(blob_list_detect))
            if number_of_blobs_detect > 0:
                for blob in blobs_list_detect:
                    blob_client_detect = container_client_detect.get_blob_client(
                        blob.name)
                    confidence = blob.name
                    blob_client_detect.delete_blob()
                break

        confidence = float(confidence)
        if confidence > 0.7:
            GPIO.output(17, True)
            GPIO.output(18, False)
        else:
            GPIO.output(17, False)
            GPIO.output(18, True)

        time.sleep(3)
        print("Press Button!!")

    GPIO.output(17, False)
    GPIO.output(18, False)