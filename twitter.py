#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  1 11:21:08 2020

@author: Felix
"""
import os
import io
import cv2
import sys
from twython import Twython
from google.cloud import vision
from google.cloud import videointelligence
from auth import (
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

twitter = Twython(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)


#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/pi/Scripts/MFPf5b20684e371.json'

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/Felix/Scripts/CameraTrap/MFPf5b20684e371.json'

"""Detect labels given a file path."""
video_client = videointelligence.VideoIntelligenceServiceClient()
features = [videointelligence.Feature.OBJECT_TRACKING] #videointelligence.Feature.LABEL_DETECTION]

path = sys.argv[-2]
#path = '/var/www/html/media/'

video_path = sys.argv[-1]
#video_path = path + 'Dec2/vi_0131_20200616_051641.mp4'

print("\nReading video {}...".format(video_path))

with open(video_path, "rb") as movie:
    input_content = movie.read()

print("\nProcessing video for object annotations...")

operation = video_client.annotate_video(
    request={"features": features, "input_content": input_content},  
)

print("\nProcessing result...")

result = operation.result(timeout=150)

print("\nFinished processing.")
print('=' * 30)

# Process object level label annotations
object_labels = result.annotation_results[0].object_annotations

trigger_tweet = False
tweetable_objects = ["animal", "bird", "cat", "sparrow", "canary", "mouse"]

trigger_bird_id = False
biggest_bbox_frame = 0

message_addendum = ''

for i, object_label in enumerate(object_labels):
    
    print("Object label description: {}".format(object_label.entity.description))
    print("\tObject Detection Confidence: {}".format(object_label.confidence))
    print("\n")

    if object_label.entity.description in tweetable_objects:
        trigger_tweet = True
        
    if "bird" in object_label.entity.description:
        print("Found a bird!")
        trigger_bird_id = True

        bird_bbox = 0.
        
        for frame in object_label.frames:
            box = frame.normalized_bounding_box
            
            bbox_width = abs(box.left - box.right)
            bbox_length = abs(box.top - box.bottom)
            bbox_area = bbox_width * bbox_length
            
            if bbox_area > bird_bbox:
                #print("Biggest Bounding Box {} and area {}".format(frame, bbox_area))
                biggest_bbox_frame = frame
                bird_bbox = bbox_area

print('=' * 30)

bbox_area = 0
#frame_counter = 0

if trigger_bird_id is True:
    
    picture_path = path + "BIRB.bmp"
        
    best_frame = round((biggest_bbox_frame.time_offset.seconds + \
                        biggest_bbox_frame.time_offset.microseconds / 1e6) * 25, 0)
    
    cam = cv2.VideoCapture(video_path)

    cam.set(1, best_frame); # Where best_frame is the frame you want
    ret, frame = cam.read() # Read the frame
    #cv2.imshow(picture_path, frame)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    cv2.imwrite(picture_path, frame) # save frame to 
    
    client = vision.ImageAnnotatorClient()
    
    with io.open(picture_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.label_detection(image=image)
    labels = response.label_annotations
    print('Advanced analysis suggests...')
    message_addendum += '\nAdvanced analysis suggests: \n'
    
    for l, label in enumerate(labels):
        print("{}".format(label.description))
        
        if l: # True for all values except for 0
            message_addendum += ', '
        
        message_addendum += label.description

print('=' * 30)

# Send a tweet if there is a tweetable_objects in video
if trigger_tweet is True:
    
    message_intro = 'Camera Trap Activated!!  I think I see...'
    
    message_assessment = ''
    for i, object_label in enumerate(object_labels):
        if object_label.confidence > 0.6 and object_label.entity.description not in message_assessment:
            message_assessment += "\n{} (Confidence: {})".format(object_label.entity.description, 
                                                                 round(object_label.confidence, 2)) 
    
    message = message_intro + message_assessment + message_addendum
    
    video = open(video_path, 'rb')
    response = twitter.upload_video(media=video, 
                                    media_type='video/mp4',
                                    media_category='tweet_video', 
                                    check_progress=True)
    media_id = [response['media_id']]
    twitter.update_status(status=message[:280], media_ids=media_id)
    
    print("Successfully tweeted:\n%s" % message)
    
else:
    print("{} was NOT tweeted out".format(video_path))
    
print("\nDone executing!")
print('=' * 30)
