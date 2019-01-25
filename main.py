#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from yoloOpencv import opencvYOLO
import cv2
import imutils
import time
from libPOS import desktop
import RPi.GPIO as GPIO 
GPIO.setmode(GPIO.BCM)

#------------------------------------------------------------------------
yolo = opencvYOLO(modeltype="yolov3-tiny", \
    objnames="cfg.breads_fake.tiny/obj.names", \
    weights="cfg.breads_fake.tiny/weights/yolov3-tiny_100000.weights",\
    cfg="cfg.breads_fake.tiny/yolov3-tiny.cfg")

labels = { "b01a":["單片土司", 8], "b01b":["雙片土司", 16], "b01c":["一包土司", 20], "b02":["熱狗夾心", 60], \
           "b03":["糖霜奶心", 42], "b04":["牛角麵包", 30], "b05":["奶油牛奶條", 55], "b06":["紅豆麵包", 35], \
           "b07":["花生夾心", 28], "b08":["小圓麵包", 18], "b09":["炸甜甜圈", 30], "b10":["鬆軟捲餅", 52], "b11":["牛肉漢堡", 85] }

idle_checkout = (8, 10)
video_out = "output.avi"
dt = desktop("images/bg.jpg", "images/bgClick.jpg")
flipFrame = (True,False) #(H, V)
#-------------------------------------------------------------------------
pinBTN = 5
GPIO.setup(pinBTN, GPIO.IN)

cv2.namedWindow("SunplusIT", cv2.WND_PROP_FULLSCREEN)        # Create a named window
cv2.setWindowProperty("SunplusIT", cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

start_time = time.time()
dt.emptyBG = None
last_movetime = time.time()  #objects > 0
YOLO = False  # YOLO detect in this loop?
txtStatus = ""

def speak(wavfile):
    os.system('/usr/bin/aplay ' + wavfile)

def dollar_speak(num):
    strNum = str(num)

    if(num<=99):
        speak("wav/number/" + str(num) + ".wav")
    elif(num<=999 and num>99):
        speak("wav/number/" + strNum[-3] + "00.wav")
        speak("wav/number/" + strNum[-2:] + ".wav")
    elif(num<=1999 and num>999):
        speak("wav/number/1000.wav")
        speak("wav/number/" + strNum[-3] + "00.wav")
        speak("wav/number/" + strNum[-2:] + ".wav")

    speak("wav/dollar_long.wav")

def speak_shoplist(itemList):
    totalPrice = 0
    for id, item in enumerate(itemList):
        itemID = item[0]
        itemName = item[1]
        itemNum = int(item[3])
        itemPrice = int(item[2])
        totalPrice += itemNum*itemPrice
        print("totalPrice:", totalPrice)

        if(itemID == "b01a"):
            if(itemNum==2):
                unit = "2_slice.wav"
            else:
                unit = "1_slice.wav"

        elif(itemID == "b01c"):
            unit = "1_pack.wav"

        else:
            if(itemNum==2):
                unit = "2_item.wav"
            else:
                unit = "1_item.wav"

        speak("wav/menu/" + itemID + ".wav")
        #speak("wav/number/" + str(itemNum) + ".wav")
        speak("wav/" + unit)
        speak("wav/number/" + str(itemNum*itemPrice) + ".wav")
        speak("wav/dollar.wav")

    speak("wav/totalis.wav")
    dollar_speak(totalPrice)

def group(items):
    """
    groups a sorted list of integers into sublists based on the integer key
    """
    if len(items) == 0:
        return []

    items.sort()
    grouped_items = []
    prev_item, rest_items = items[0], items[1:]

    subgroup = [prev_item]
    for item in rest_items:
        if item != prev_item:
            grouped_items.append(subgroup)
            subgroup = []
        subgroup.append(item)
        prev_item = item

    grouped_items.append(subgroup)
    return grouped_items

if __name__ == "__main__":

    INPUT = cv2.VideoCapture(0)

    width = int(INPUT.get(cv2.CAP_PROP_FRAME_WIDTH))   # float
    height = int(INPUT.get(cv2.CAP_PROP_FRAME_HEIGHT)) # float

    #fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    #out = cv2.VideoWriter(video_out,fourcc, 30.0, (int(width),int(height)))

    frameID = 0
    while True:
        hasFrame, frame = INPUT.read()
        # Stop the program if reached end of video
        if not hasFrame:
            print("Done processing !!!")
            print("--- %s seconds ---" % (time.time() - start_time))
            break


        '''
        yolo.getObject(frame, labelWant="", drawBox=True, bold=1, textsize=0.6, bcolor=(0,0,255), tcolor=(255,255,255))
        #print ("Object counts:", yolo.objCounts)
        #yolo.listLabels()
        #print("classIds:{}, confidences:{}, labelName:{}, bbox:{}".\
        #    format(len(yolo.classIds), len(yolo.scores), len(yolo.labelNames), len(yolo.bbox)) )
        #cv2.imshow("Frame", imutils.resize(frame, width=600))
        '''

        #objects = dt.getContours(frame, 1200)
        #print("Objects:", objects)
        if(flipFrame[0] is True):
            frame = cv2.flip(frame, 1 , dst=None)
        elif(flipFrame[1] is True):
            frame = cv2.flip(frame, 0 , dst=None)

        if(dt.emptyBG is None or time.time()-dt.emptyBG_time>=0.5):
            dt.emptyBG = frame.copy()
            dt.emptyBG_time = time.time()
            #print("Update BG")

        objects = dt.difference(dt.emptyBG, frame, 800)
        if(objects>0):
            last_movetime = time.time()
            timeout_move = str(round(time.time()-last_movetime, 0))
            txtStatus = "Idle:" + timeout_move
        else:
            waiting = time.time() - last_movetime
            timeout_move = str(round(time.time()-last_movetime, 0))
            txtStatus = "Idle:" + timeout_move

            if( (waiting > idle_checkout[0] and waiting<idle_checkout[1]) or GPIO.input(pinBTN)==1  ):
                txtStatus = "Caculate"
                YOLO = True

        imgDisplay = dt.display(frame.copy(), txtStatus)
        cv2.imshow("SunplusIT", imgDisplay)
        cv2.waitKey(1)

        if(YOLO is True):
            yoloStart = time.time()
            print("YOLO start...")
            speak("wav/start_pos.wav")
            YOLO = False
            yolo.getObject(frame, labelWant="", drawBox=False, bold=1, textsize=0.6, bcolor=(0,0,255), tcolor=(255,255,255))


            for id, label in enumerate(yolo.labelNames):
                x = yolo.bbox[id][0]
                y = yolo.bbox[id][1]
                w = yolo.bbox[id][2]
                h = yolo.bbox[id][3]
                cx = int(x+w/3)
                cy = int(y+h/3)
                frame = desktop.printText(desktop, txt=labels[label][0], bg=frame, color=(255,255,255,0), size=0.65, pos=(cx,cy), type="Chinese")

            #print("classIds:{}, confidences:{}, labelName:{}, bbox:{}".\
            #    format(len(yolo.classIds), len(yolo.scores), len(yolo.labelNames), len(yolo.bbox)) )
            if(len(yolo.labelNames)>0):
                types = group(yolo.labelNames)
                print("Labels:", types)
                shoplist = []
                for items in types:
                    shoplist.append([items[0], labels[items[0]][0], labels[items[0]][1], len(items)])
                    #desktop.printText(labels[items[0]][0], frame, color=(255,255,0,0), size=0.6, pos=(0,0), type="Chinese")

                txtStatus = "checkout"
                print(shoplist)

                imgDisplay = dt.display(frame, txtStatus, shoplist)
                cv2.imshow("SunplusIT", imgDisplay)
                cv2.waitKey(1)
                if(len(shoplist)>0):
                    print("YOLo used:" + str(round(time.time()-yoloStart, 3)))
                    print("Shop list:", shoplist)
                    cv2.waitKey(1)
                    speak_shoplist(shoplist)

                    #time.sleep(10)

                #cv2.imshow("SunplusIT", imgDisplay)
                #cv2.waitKey(1)
                #time.sleep(0)

        #dt.emptyBG = frame.copy()
        #dt.emptyBG_time = time.time()
        #if(video_out!=""):
        #out.write(frame)
        
        k = cv2.waitKey(1)
        if k == 0xFF & ord("q"):
            out.release()
            break
