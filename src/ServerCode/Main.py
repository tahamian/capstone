from collections import deque
import threading
import time
import queue

from imutils.video import VideoStream
import numpy as np
import cv2
import imutils
import argparse

from Communication import runCommunication
import Parameters
import Location

regionSizeX = 1
regionSizeY = 1

def handleComEvent(queue):
    if queue.empty():
        return

    item = queue.get()

    if not (item.recipient == 'MAIN'):
        queue.put(item)
        return

    elif (item.command == 'RECORD_MEASUREMENT'):
        print()
        # Record a measurement

    elif (item.command == 'GET_NEXT_LOCATION'):
        newCommand = {
            'recipient': 'COM',
            'command': 'SEND_NEW_LOCATION',
            'location': nextLocation(rawLocation)
        }

def createRegions():
    regions = np.full([Parameters.NUM_REGIONS_X, Parameters.NUM_REGIONS_Y], {})

    for i in range(0, regions.shape[0]):
        for j in range(0, regions.shape[1]):
            region = {'visited': False }

            x = (i / Parameters.NUM_REGIONS_X) * (1.5) * (regionSizeX)
            y = (j / Parameters.NUM_REGIONS_Y) * (1/5) * (regionSizeY)

            region['center'] = (x, y)

            regions[i][j] = region

    return regions

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video",
    help="path to the (optional) video file")
    ap.add_argument("-b", "--buffer", type=int, default=64,
    help="max buffer size")
    args = vars(ap.parse_args())

    # if a video path was not supplied, grab the reference
    # to the webcam
    if not args.get("video", False):
        vs = VideoStream(src=0).start()

    # otherwise, grab a reference to the video file
    else:
        vs = cv2.VideoCapture(args["video"])

    queue_communication = queue.Queue()
    event_communication = threading.Event()
    event_communication.queue = queue_communication

    thread_communication = threading.Thread(
        name='communication',
        target=runCommunication,
        args=(event_communication,)
    )

    thread_communication.start()

    regions = createRegions()
    rawLocation = (-1, -1)

    # Let the webcam warm up
    time.sleep(2.0)

    while True:
        handleComEvent(queue_communication)

        frame = vs.read()

        if frame is None:
            break

        frame = imutils.resize(
            frame,
            width=Parameters.CAMERA_RES_W,
            height=Parameters.CAMERA_RES_H
        )

        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, Parameters.COLOR_LOWER, Parameters.COLOR_UPPER)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        cnts = cv2.findContours(
            mask.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        cnts = imutils.grab_contours(cnts)
        center = None

        if len(cnts) > 0:
            # find the largest contour in the mask, then use
            # it to compute the minimum enclosing circle and
            # centroid
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # only proceed if the radius meets a minimum size
            if radius > Parameters.MIN_RADIUS and radius < Parameters.MAX_RADIUS:
                # draw the circle and centroid on the frame,
                # then update the list of tracked points
                cv2.circle(frame, (int(x), int(y)), int(radius),
                            (0, 255, 255), 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)

                rawLocation = center

        # show the frame to our screen
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the 'q' key is pressed, stop the loop
        if key == ord("q"):
            break

        time.sleep(0.1)

    vs.stop()

    cv2.destroyAllWindows()