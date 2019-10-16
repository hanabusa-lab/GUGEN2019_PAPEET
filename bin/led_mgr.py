# -*- coding: utf-8 -*-
from time import sleep
import time
import os
import json
import pprint
import threading
import signal
import sys
from neopixel import *
from papeet_def import *
import datetime
import fasteners
import board

#定数定義
SAMPLING_TIME=0.2           #サンプリングタイム
LED_REQ='../dat/led_req.json' #LEDリクエストファイル
# LED pixels configuration:
#LED_COUNT      = 16      # Number of LED pixels.
LED_COUNT      = 1      # Number of LED pixels.
LED_PIN        = board.D12      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
#LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
#LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
#LED_BRIGHTNESS = 25     # Set to 0 for darkest and 255 for brightest
#LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
#LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

LED_ORDER = GRB
LED_BRIGHT = 0.4

#グローバル変数
gthread_led = ""
gthread_enablefg = True #スレッドの有効フラグ
gled_cntrl = 0  #0:None, 1:START, 2:STOP
gled_pattern = 0
gled_time = 0
gled_color = (0,0,0)
gpre_led_color = (0,0,0)
gled_start_time = None
glock =""   #Lockファイル

#ロックファイルのパス
LOCK_FILE = '/tmp/lockfile_led'


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return (r, g, b) if ORDER == neopixel.RGB or ORDER == neopixel.GRB else (r, g, b, 0)


def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

# Define functions which animate LEDs in various ways.
def color_wipe(pixels, color, wait_ms=50):
    pixels.fill(color)
    pixels.show()
    time.sleep(wait_ms/1000.0)

    """Wipe color across display a pixel at a time."""
    """
    for i in range(pixels.numPixels()):
        pixels.setPixelColor(i, color)
        pixels.show()
        time.sleep(wait_ms/1000.0)
    """

def color_bright(pixels, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for j in range(5):
        for i in range(len(pixels)):
            if (i+j)%2 == 0 :
                pixels[i]=color
            else :
                pixels[i]=(0,0,0)
            pixels.show()
        time.sleep(wait_ms/1000.0)

def color_bright2(pixels, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for j in range(20):
        for i in range(len(pixels)):
            if (i+j)%2 == 0 :
                pixels[i]=color
            else :
                pixels[i]=(0,0,0)
            pixels.show()
        time.sleep(wait_ms/1000.0)


#jsonファイルのパース処理
def parse_req_file(filename) :
    with open(LED_REQ) as f:
        d = json.load(f)
    pprint.pprint(d, width=40)
    return d

#LEDスレッド
def exec_led_thread() :
    global gthread_enablefg, gled_cntrl, gled_pattern, gled_time, gled_color, gled_start_time, gpre_led_color

    # Create NeoPixel object with appropriate configuration.
    #pixels = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).

    pixels = NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHT, auto_write=False,
                           pixel_order=LED_ORDER)
    #pixels.begin()
    #clear pre color
    #colorWipe(pixels, Color(0, 0, 0))
    pixels.fill((0, 0, 0))
    pixels.show()

    while 1 :
        if gthread_enablefg == False :
            color_wipe(pixels, (0, 0, 0))
            print("end exec_led_thread")
            return

        #停止処理の場合
        #基本的に何も処理がない場合には、ここの処理に入る。
        if gled_cntrl ==  LEDCntrl.STOP:
            #print("thred gled_stop")
            color_wipe(pixels, (0, 0, 0))
            sleep(SAMPLING_TIME)
            continue

        #経過時間のチェック
        if gled_start_time != None and gled_time > 0:
            now = datetime.datetime.now()
            diftime = now - gled_start_time
            if diftime.total_seconds() > gled_time :
                color_wipe(pixels, (0, 0, 0))
                sleep(SAMPLING_TIME)
                gled_start_time = None
                gled_cntrl = LEDCntrl.STOP
                print("thred time passed")
                continue

        #モードごとの実行
        if gled_pattern == LEDPattern.WIPE :
            #print("thread exec color Wipe ", gled_color)
            if gled_color != gpre_led_color :
                print("update color")
                color_wipe(pixels, (gled_color[1], gled_color[0], gled_color[2]))
                gpre_led_color = gled_color

            sleep(SAMPLING_TIME)
            continue

        if gled_pattern == LEDPattern.BRIGHT :
            #print("thread exec color Bright ", gled_color)
            color_bright(pixels, (gled_color[1], gled_color[0], gled_color[2]), 500)

        if gled_pattern == LEDPattern.BRIGHT2:
            #print("thread exec color Bright2 ", gled_color)
            color_bright2(pixels, (gled_color[1], gled_color[0], gled_color[2]))


#LEDコントロール情報の更新
def update_led_cntrl(d):
    global gled_cntrl, gled_pattern, gled_time, gled_color, gled_start_time

    print("exec_led_cnrl arg=",d)

    #コントロールモードの確認
    if d.get('CNTRL') != None :
         gled_cntrl = int(d.get('CNTRL'))
         print("cntl=", gled_cntrl)

    #実行パターンの確認
    if d.get('PATTERN') != None :
         gled_pattern = int(d.get('PATTERN'))

    #色の確認
    if d.get('COLOR') != None :
         gled_color = (d.get('COLOR')[0], d.get('COLOR')[1], d.get('COLOR')[2])

    #時間の確認
    if d.get('TIME') != None :
        gled_time = float(d.get('TIME'))
        #Timeが指定されている場合には時間を更新する。
        gled_start_time =  datetime.datetime.now()
    else :
        #Timeが設定されていない場合には、開始時間をNoneに設定する。
        gled_start_time = None

    print("update_led_cntrl. cntrl",gled_cntrl, "pattern", gled_pattern, "time", gled_time, "color", gled_color)

#終了処理
def handler(signal, frame):
    global gthread_led, gthread_enablefg
    gthread_enablefg = False
    gthread_led.join()
    print('exit')
    sys.exit(0)

#mainプログラム
if __name__== '__main__':
    #write json test

    #ロックファイルの作成
    glock = fasteners.InterProcessLock(LOCK_FILE)
    """
    d={'PATTERN':1, 'COLOR':(1,2,3), 'CNTRL':'1', 'TIME':20}
    print(d)
    with open('../dat/led_req.json', 'w') as f:
        json.dump(d, f, indent=4)
    """
    """
    print("enum test", LEDCntrl.NONE)
    if LEDCntrl.NONE == 0 :
        print("enum test ok", LEDCntrl.NONE)
    """

    #シグナルハンドラの登録(Cntrl+Cを受け取った際の終了処理)
    signal.signal(signal.SIGINT, handler)


    #LEDスレッドの作成と実行
    gthread_led = threading.Thread(target=exec_led_thread)
    gthread_led.start()

    #実行ループ(ファイルチェック)
    while 1 :
        #print("file check")
        #check conf file
        if os.path.exists(LED_REQ) == True :
            print("file exist")
            #内容の確認の前に、ファイルの上書きをされると、指示が正しく反映されないため、ロックファイルを用いる
            glock.acquire()
            d=parse_req_file(LED_REQ)
            update_led_cntrl(d)
            os.remove(LED_REQ)
            glock.release()


        sleep(SAMPLING_TIME)
