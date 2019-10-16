# -*- coding: utf-8 -*-
from time import sleep
import time
import os
import  json
import pprint
import threading
import signal
import sys
from papeet_def import *
import datetime
import fasteners

from gpiozero import Servo
from aiy.pins import PIN_A
from aiy.pins import PIN_B
from aiy.pins import PIN_C
from aiy.pins import PIN_D


#定数定義
SAMPLING_TIME=0.3           #サンプリングタイム
SERV_REQ='../dat/serv_req.json' #SERVリクエストファイル
SERV_IO = 0 #SERVOのGPIO
#SERVD_PATH = "/pet/bin/PiBits/ServoBlaster/user/servod"

#グローバル変数
gthread_serv = ""
gthread_enablefg = True #スレッドの有効フラグ
gserv_start_time = None
gserv_cntrl = ""
gserv_pattern = ""
gserv_time = None
gserv_type = 0
gserv = []  #サーボクラス
glock =None   #Lockファイル

#一時的なサーボクラス
tserv = None

LOCK_FILE = '/tmp/lockfile_serv'

#SERVを滑らかに動作する際のSAMPLING_TIME
SMOOTH_SAMPLING_TIME = 0.02
#SERVを滑らかに駆動する際の単位時間あたりのs(大きくするとゆっくる)
SMOOTH_SAMPLING_SCALE = 20.0


#jsonファイルのパース処理
def parse_req_file(filename) :
    with open(SERV_REQ) as f:
        d = json.load(f)
    pprint.pprint(d, width=40)
    return d

#サーボ駆動 val (0-100%)
def serv_move(stype, val) :
    global gserv
    #cmd="echo "+str(SERV_IO)+"="+str(val)+"% | sudo tee /dev/servoblaster"
    #os.system(cmd)
    #print(datetime.datetime.now() , "serv_mov", cmd)
    gserv[stype].value = val

#サーボ駆動(滑らか)
def serv_smooth_move(stype, sval, eval) :
    global gserv
    fg = 1
    if  sval == eval :
        return;
    if eval < sval :
        fg = -1

    for i in range((int)(sval*SMOOTH_SAMPLING_SCALE), int(eval*SMOOTH_SAMPLING_SCALE), fg):
        value = float((i)/(SMOOTH_SAMPLING_SCALE))
        #print("smooth move",value)
        gserv[stype].value = value
        sleep(SMOOTH_SAMPLING_TIME)

#Servスレッド
def exec_serv_thread() :
    global gthread_enablefg, gserv_cntrl, gserv_pattern, gserv_time, gserv_start_time, gserv, tserv, gserv_type
    serv_val_def = 50
    #サーボの値を初期化位置に設定する。
    serv_val = serv_val_def
    serv_dir = 1
    #serv_div = 2    #サーボ移動の分解能
    #serv_sampling_time = 0.1 #スキャン時のサンプリング時間
    serv_div = 40    #サーボ移動の分解能
    serv_sampling_time = 0.5 #スキャン時のサンプリング時間

    pre_body_val = 0
    while 1 :
        print("thread", gserv_cntrl, gserv_pattern, gserv_start_time, gserv_time)
        if gthread_enablefg == False :
            print("end exec_serv_thread")
            return

        #ON要求がる場合
        if gserv_cntrl ==  ServCntrl.ON:
            print("cntl = on gserv_type=", gserv_type)
            #対象のサーボをOFFする。
            if gserv_type <= len(gserv) :
                serv_move(gserv_type, 0)
            #offしたら、stopに遷移する。
            gserv_cntrl =  ServCntrl.STOP

        #OFF要求がる場合
        if gserv_cntrl ==  ServCntrl.OFF:
            print("cntl = off gserv_type=", gserv_type)
            #対象のサーボをOFFする。
            if gserv_type <= len(gserv) :
                serv_move(gserv_type, None)
            #offしたら、stopに遷移する。
            gserv_cntrl =  ServCntrl.STOP


        #停止処理の場合
        if gserv_cntrl ==  ServCntrl.STOP:
            print("cntrl = stop")
            sleep(SAMPLING_TIME)
            continue

        #経過時間のチェック
        if gserv_start_time != None and gserv_time > 0:
            now = datetime.datetime.now()
            diftime = now - gserv_start_time
            print("check time", diftime, gserv_time)

            if diftime.total_seconds() > gserv_time :
                sleep(SAMPLING_TIME)
                serv_val = serv_val_def
                gserv_start_time = None
                gserv_cntrl =  ServCntrl.STOP
                print("pass time")
                continue

        if gserv_pattern == ServPattern.MOUSE_OPEN :
            print("HEAD open")
            serv_move(ServType.MOUSE, 0.5)
            sleep(1)

        if gserv_pattern == ServPattern.MOUSE_CLOSE :
            print("HEAD close")
            #closeをvalue 0 状態にする。
            serv_move(ServType.MOUSE, 0)
            sleep(1)

        if gserv_pattern == ServPattern.MOUSE_PAKUPAKU :
            print("MOUSE pakupaku")
            serv_move(ServType.MOUSE, 0)
            sleep(0.2)
            serv_move(ServType.MOUSE, 0.5)
            sleep(0.2)
            serv_move(ServType.MOUSE, 0)
            sleep(0.2)
            serv_move(ServType.MOUSE, 0.5)
            sleep(0.2)
            serv_move(ServType.MOUSE, 0)
            sleep(0.5)
            #電源スリープ
            serv_move(ServType.MOUSE, None)

        if gserv_pattern == ServPattern.HEAD_CENTER :
            print("head center")
            serv_move(ServType.HEAD, 0)
            sleep(1)

        if gserv_pattern == ServPattern.HEAD_UP :
            print("head up")
            #closeをvalue 0 状態にする。
            serv_move(ServType.HEAD, 0.5)
            sleep(1)

        if gserv_pattern == ServPattern.HEAD_DOWN :
            print("head down")
            #closeをvalue 0 状態にする。
            serv_move(ServType.HEAD, -0.5)
            sleep(1)

        if gserv_pattern == ServPattern.HEAD_UNUN :
            print("head unun")
            serv_move(ServType.HEAD, 0)
            sleep(0.2)
            serv_move(ServType.HEAD, -0.5)
            sleep(0.2)
            serv_move(ServType.HEAD, 0)
            sleep(0.2)
            serv_move(ServType.HEAD, -0.5)
            sleep(0.2)
            serv_move(ServType.HEAD, 0)
            sleep(0.5)
            #電源スリープ
            serv_move(ServType.HEAD, None)

        if gserv_pattern == ServPattern.BODY_CENTER :
            print("body center")
            #closeをvalue 0 状態にする。
            serv_smooth_move(ServType.BODY, pre_body_val, 0)
            serv_move(ServType.BODY, None)
            pre_body_val = 0

        if gserv_pattern == ServPattern.BODY_RIGHT :
            print("body right")
            #closeをvalue 0 状態にする。
            serv_smooth_move(ServType.BODY, pre_body_val, 0.9)
            pre_body_val = 0.9

        if gserv_pattern == ServPattern.BODY_RIGHT_SMALL :
            print("body right small")
            #closeをvalue 0 状態にする。
            serv_smooth_move(ServType.BODY, pre_body_val, 0.5)
            pre_body_val = 0.5

        if gserv_pattern == ServPattern.BODY_LEFT :
            print("body left")
            #closeをvalue 0 状態にする。
            serv_smooth_move(ServType.BODY, pre_body_val, -0.9)
            pre_body_val = -0.9

        if gserv_pattern == ServPattern.BODY_LEFT_SMALL :
            print("body left small")
            #closeをvalue 0 状態にする。
            serv_smooth_move(ServType.BODY, pre_body_val, -0.5)
            pre_body_val = -0.5

        if gserv_pattern == ServPattern.BODY_SWING :
            print("body swign")
            #closeをvalue 0 状態にする。
            serv_smooth_move(ServType.BODY, pre_body_val, 0)
            serv_smooth_move(ServType.BODY, 0, 0.5)
            serv_smooth_move(ServType.BODY, 0.5, -0.5)
            serv_smooth_move(ServType.BODY, -0.5, 0)
            serv_move(ServType.BODY, None)

            pre_body_val = 0

            #serv_move(ServType.BODY, None)


        #print("sleep thread")
        sleep(SAMPLING_TIME)

#SERVコントロール情報の更新
def update_serv_cntrl(d):
    global gserv_cntrl, gserv_pattern, gserv_time, gserv_type, gserv_start_time

    print("update serv arg=",d)

    #コントロールモードの確認
    if d.get('CNTRL') != None :
         gserv_cntrl = int(d.get('CNTRL'))

    #実行パターンの確認
    if d.get('PATTERN') != None :
         gserv_pattern = int(d.get('PATTERN'))

    #時間の確認
    if d.get('TIME') != None :
        gserv_time = int(d.get('TIME'))
        #Timeが指定されている場合には時間を更新する。
        gserv_start_time =  datetime.datetime.now()
    else :
        #Timeが設定されていない場合には、開始時間をNoneに設定する。
        gserv_start_time = None

    if d.get('TYPE') != None :
        gserv_type = int(d.get('TYPE'))

    print("update_serv_cntrl. cntrl",gserv_cntrl, "pattern", gserv_pattern, "time", gserv_time, "type")

#終了処理
def handler(signal, frame):
    global gthread_serv, gthread_enablefg
    gthread_enablefg = False
    gthread_serv.join()
    #kill serv
    #cmd="sudo killall servod"
    #os.system(cmd)

    #サーボを順次落としましょう
    for i in range(len(gserv)) :
        serv_move(i, 0)
        print("stopping ",i)
        sleep(1)
        serv_move(i, None)
        sleep(1)

    print('exit')
    sys.exit(0)

#サーボの初期化処理
def init_serv() :
    global gserv, tserv
    print("start serv init")

    gserv.append(Servo(PIN_A, initial_value=0, min_pulse_width=.0006, max_pulse_width=.0024))
    serv_move(ServType.MOUSE, 0)
    sleep(1)
    serv_move(ServType.MOUSE, None)

    #Noneを指定すると、サーボへのパルス指定をオフできて、余計な電流が流れない。
    #ただし、再開するには、0を指定する必要あり。

    gserv.append(Servo(4, initial_value=0, min_pulse_width=.0006, max_pulse_width=.0024))
    serv_move(ServType.HEAD, 0)
    sleep(1)
    serv_move(ServType.HEAD, None)

    #gserv.append(Servo(PIN_D, initial_value=0, min_pulse_width=.0006, max_pulse_width=.0024))
    gserv.append(Servo(PIN_B, initial_value=0, min_pulse_width=.0006, max_pulse_width=.0024))

    serv_move(ServType.BODY, 0)
    sleep(1)
    serv_move(ServType.BODY, None)
    print("end serv init")


    #tserv=Servo(PIN_A, min_pulse_width=.0006, max_pulse_width=.0024)


    #gserv.append(Servo(PIN_C, min_pulse_width=.0006, max_pulse_width=.0024))
    #serv_move(ServType.BODY, 0)
    #sleep(2)


    pass

#mainプログラム
if __name__== '__main__':
    #ロックファイル生成
    glock = fasteners.InterProcessLock(LOCK_FILE)

    #サーボの初期化処理
    init_serv()

    #シグナルハンドラの登録(Cntrl+Cを受け取った際の終了処理)
    signal.signal(signal.SIGINT, handler)

    #Servスレッドの作成と実行
    gthread_serv = threading.Thread(target=exec_serv_thread)
    gthread_serv.start()

    #実行ループ(ファイルチェック)
    while 1 :
        #check conf file
        if os.path.exists(SERV_REQ) == True :
            #内容の確認の前に、ファイルの上書きをされると、指示が正しく反映されないため、ロックファイルを用いる
            glock.acquire()
            d=parse_req_file(SERV_REQ)
            update_serv_cntrl(d)
            os.remove(SERV_REQ)
            glock.release()

        sleep(SAMPLING_TIME)
