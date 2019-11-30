import sys
import locale
import subprocess
import time
import logging
import datetime
from enum import IntEnum
import fasteners
import json
import os
import requests
import re
import jaconv
import timeout_decorator
import base64
import picamera
#from goto import goto, label

from aiy.board import Board, Led
from aiy.cloudspeech import CloudSpeechClient

from sentiment_google import SentimentGoogle
from behavior import Behavior
from papeet_def import *

#サーボリクエストのフラグ
SERV_ENABLE_FG = True
# サーバーのIPアドレス
SERV_IP = "192.168.3.7:5000"

#sleepのサンプリングタイム
SLEEP_SAMPLING_TIME = 0.5

#感情分析のしきい値
SENTIMENT_THRETHOLD = 0.4

#LED関連
#LEDのリクエストファイル
LED_REQ_FILE = "../dat/led_req.json"
#LEDのロックファイル
LED_LOCK_FILE = '/tmp/lockfile_led'

#サーボのリクエストファイル
SERV_REQ_FILE = "../dat/serv_req.json"
#サーボのロックファイル
SERV_LOCK_FILE = '/tmp/lockfile_serv'

AFTER_WAIT_RESTART ='../dat/restart'

#LED用ロックファイル
gled_lockfile = None

#サーボ用のロックファイル
gserv_lockfile = None

class BehaviorMode(IntEnum):
    GREETING = 1
    PRE_ORDER = 2
    WAITING_DISH =3
    AFTER_EAT = 4
    SURVEY = 5
    CHECK_BILL = 6

gmode = BehaviorMode.SURVEY
gclient = None
gboard = None
glanguage = None
#前に聞いた文章
gpre_text = ""

gcamera = "" #カメラオブジェクト

def jtalk_create_message(t):
    open_jtalk=['open_jtalk']
    mech=['-x','/var/lib/mecab/dic/open-jtalk/naist-jdic']
    #htsvoice=['-m','/usr/share/hts-voice/mei/mei_normal.htsvoice']
    #htsvoice=['-m','/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice']
    htsvoice=['-m','/usr/share/hts-voice/yoe/yoe.htsvoice']
    speed=['-r','1.0']
    #outwav=['-ow','../dat/open_jtalk.wav']
    #テキストのエンコード
    enc_txt = str(base64.urlsafe_b64encode(t.encode('utf-8')))
    print("enc_txt", enc_txt)

    #ファイルがあったら処理を抜ける
    path = '../voice/'+enc_txt+'.wav'
    if os.path.exists(path) == True :
        return

    outwav=['-ow',path]
    cmd=open_jtalk+mech+htsvoice+speed+outwav
    c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    c.stdin.write(t.encode())
    c.stdin.close()
    c.wait()
    #aplay = ['aplay','-q','../dat/open_jtalk.wav']
    #wr = subprocess.Popen(aplay)
    #wr.wait()

def jtalk_say_message(t):
    """
    open_jtalk=['open_jtalk']
    mech=['-x','/var/lib/mecab/dic/open-jtalk/naist-jdic']
    #htsvoice=['-m','/usr/share/hts-voice/mei/mei_normal.htsvoice']
    #htsvoice=['-m','/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice']
    htsvoice=['-m','/usr/share/hts-voice/yoe/yoe.htsvoice']
    speed=['-r','1.0']
    outwav=['-ow','../dat/open_jtalk.wav']
    cmd=open_jtalk+mech+htsvoice+speed+outwav
    c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    c.stdin.write(t.encode())
    c.stdin.close()
    c.wait()
    """
    #テキストのファイル名で実行する
    enc_txt = str(base64.urlsafe_b64encode(t.encode('utf-8')))
    #aplay = ['aplay','-q','../dat/open_jtalk.wav']
    aplay = ['aplay','-q','../voice/'+enc_txt+'.wav']

    wr = subprocess.Popen(aplay)
    wr.wait()


#LEDの動作依頼
def exec_led(mode) :
    global gled_lockfile

    #LEDリクエストファイルの作成
    if mode == 1 :
        #mode 1. 白点灯
        d={'PATTERN':int(LEDPattern.WIPE), 'COLOR':(255, 255, 255), 'CNTRL':int(LEDCntrl.START), 'TIME':10}
    elif mode == 2:
        #mode 2. 黄色点滅
        d={'PATTERN':int(LEDPattern.WIPE), 'COLOR':(255, 255, 0), 'CNTRL':int(LEDCntrl.START), 'TIME':10}

    print(d)
    gled_lockfile.acquire()
    with open(LED_REQ_FILE, 'w') as f:
        json.dump(d, f, indent=4)
    gled_lockfile.release()

#LEDの停止依頼
def exec_led_stop() :
    global gled_lockfile

    print("off request")
    d={'CNTRL':int(LEDCntrl.STOP)}
    print(d)
    gled_lockfile.acquire()
    with open(LED_REQ_FILE, 'w') as f:
        json.dump(d, f, indent=4)
    gled_lockfile.release()

#Serv(Mouse部)の動作依頼
def exec_mouse(mode) :
    global gserv_lockfile

    #Servリクエストファイルの作成
    if mode == 1 :
        #mode 1. 白点灯
        d={'PATTERN':int(ServPattern.MOUSE_PAKUPAKU), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
    if mode == 2 :
        #mode 1. 白点灯
        d={'PATTERN':int(ServPattern.HEAD_UNUN), 'CNTRL':int(LEDCntrl.START), 'TIME':1}

    print(d)
    gserv_lockfile.acquire()
    with open(SERV_REQ_FILE, 'w') as f:
        json.dump(d, f, indent=4)
    gserv_lockfile.release()

#Serv(Head部)の動作依頼
def exec_head(mode) :
    global gserv_lockfile

    #Servリクエストファイルの作成
    if mode == 1 :
        #mode 1. 白点灯
        d={'PATTERN':int(ServPattern.HEAD_UNUN), 'CNTRL':int(LEDCntrl.START), 'TIME':1}

    print(d)
    gserv_lockfile.acquire()
    with open(SERV_REQ_FILE, 'w') as f:
        json.dump(d, f, indent=4)
    gserv_lockfile.release()


#Serv(Body部)の動作依頼
def exec_body(mode) :
    global gserv_lockfile

    #Servリクエストファイルの作成
    if mode == 1 :
        #mode 1. 白点灯
        d={'PATTERN':int(ServPattern.BODY_SWING_SMALL), 'CNTRL':int(LEDCntrl.START), 'TIME':1}

    print(d)
    gserv_lockfile.acquire()
    with open(SERV_REQ_FILE, 'w') as f:
        json.dump(d, f, indent=4)
    gserv_lockfile.release()

#サーバへ送付するテキストの送付
def send_say_text(text) :
    if SERV_ENABLE_FG == True :
        cmd = "curl -X POST -H 'Accept:application/json' -H 'Content-Type:application/json' -d '{\"TYPE\":\"1\", \"TEXT\":\""+text+"\"}' "+SERV_IP
        print("serv send=",cmd)
        os.system(cmd)
#サーバへ送付するテキストの送付
def listen_say_text(text) :
    if SERV_ENABLE_FG == True :
        cmd = "curl -X POST -H 'Accept:application/json' -H 'Content-Type:application/json' -d '{\"TYPE\":\"2\", \"TEXT\":\""+text+"\"}' "+SERV_IP
        print("serv send=",cmd)
        os.system(cmd)

#サーバへ送付するテキストの送付
def monitor_clear() :
    if SERV_ENABLE_FG == True :
        cmd = "curl -X POST -H 'Accept:application/json' -H 'Content-Type:application/json' -d '{\"TYPE\":\"6\"}' "+SERV_IP
        print("serv send=",cmd)
        os.system(cmd)

#写真撮影
def exec_picture() :


    speech_text="写真とるよ"
    #音の読み上げ
    jtalk_create_message(speech_text)
    send_say_text(speech_text)
    jtalk_say_message(speech_text)

    speech_text="ハイ"
    #音の読み上げ
    jtalk_create_message(speech_text)
    send_say_text(speech_text)
    jtalk_say_message(speech_text)

    speech_text="チーズ"
    #音の読み上げ
    jtalk_create_message(speech_text)
    send_say_text(speech_text)
    jtalk_say_message(speech_text)

    global gcamera
    now= datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = '/home/pi/papeet/img/'+now+".jpg"
    print("filename=", filename)
    #cmd = 'raspistill -w 1200 -h 900 -n -t 10 -q 100 -e jpg -o '+filename
    #os.system(cmd)
    #画像の取得
    gcamera.capture(filename)
    time.sleep(1)

    if SERV_ENABLE_FG == True :
        cmd = "curl -X POST -F \"img=@"+filename+";type=img/jpg\" "+SERV_IP+"/send"
        print("serv send=",cmd)
        os.system(cmd)

#振る舞いノードの実行
def exec_behavior_node(node):
    global gpre_text
    print(node)

    #次の条件分岐で用いる
    score = 0

    #ledの実行
    led_mode = int(node['led_mode'])
    if led_mode != 0 :
        print('exec led')
        exec_led(led_mode)

    #pre sleepの実行
    pre_wait = int(node['pre_wait'])
    if pre_wait != 0 :
        print("pre wait", pre_wait)
        st=datetime.datetime.now()
        while(True) :
            time.sleep(SLEEP_SAMPLING_TIME)
            now=datetime.datetime.now()
            delta = now - st
            if delta.seconds > pre_wait :
                break;

    #会話の実行
    speech_text = node['speech_text']
    #i = len(speech_text)
    #print("speeth len", type(speech_text), speech_text, len(speech_text))
    if 'pretext' in speech_text and gpre_text is not None:
        speech_text = speech_text.replace('pretext', gpre_text)
        print("say pre text=", gpre_text,' new text=', speech_text)

    if len(speech_text) > 0 :
        logging.info('speech_text'+speech_text)
        #ToDo保存してある過去の音声ファイルが存在する場合には読み込んで実行すること
        jtalk_create_message(speech_text)

        #サーボの実行
        mouse_mode = int(node['mouse_mode'])
        if mouse_mode != 0 :
            print('exec mouse')
            exec_mouse(mouse_mode)

        #サーバへテキストの送付
        send_say_text(speech_text)

        #音の読み上げ
        jtalk_say_message(speech_text)


    #ledの停止処理
    #if led_mode != 0 :
    #    print('exec led_stop')
    #    exec_led_stop()

    #聞いた後の頷き
    head_mode = int(node['head_mode'])
    if  head_mode != 0 :
        print('exec head-------------')
        exec_head(head_mode)

    #認識の実行
    listening_mode = int(node['listening_mode'])
    if listening_mode != 0 :
        print("start listening")
        text = gclient.recognize(language_code=glanguage,hint_phrases=None)
        if text is None:
            logging.info('You said nothing.')
            score = -1
        else :
            logging.info('You said: "%s"' % text)
            listen_say_text(text)
            #前の文章の保存
            gpre_text = text

    #感情分析の実行
    sentiment_mode = int(node['sentiment_mode'])
    if sentiment_mode != 0:
        response = SentimentGoogle().sentiment(gpre_text)
        print("sentence=", gpre_text, "sentiment respose", response, "score", response['score'])
        score = response['score']

    #bodyの実行
    try :
        body_mode = int(node['body_mode'])
        if body_mode != 0:
            print("exec body")
            exec_body(body_mode)
    except :
        print("body_mode does not exist")

    #after sleepの実行
    after_wait = int(node['after_wait'] or 0)

    if after_wait == -1:
        #after_waitが-1の場合には、dat/restartファイルができるまで、待ち状態にする。
        while(True) :
            if os.path.exists(AFTER_WAIT_RESTART ) == True :
                os.remove(AFTER_WAIT_RESTART )
                break
            print("waiting after wait restart file")
            time.sleep(SLEEP_SAMPLING_TIME)
    if after_wait != 0 :
        print("after wait", after_wait)
        st=datetime.datetime.now()
        while(True) :
            time.sleep(SLEEP_SAMPLING_TIME)
            now=datetime.datetime.now()
            delta = now - st
            if delta.seconds > after_wait :
                break;
    #最後の処理に抜ける場合

    #次のnodeの取得
    #次のノードを分岐するときには?で、次のインデックスが区切られています。
    if '?' in str(node['next_node']) :
        tmp_index = str(node['next_node']).split('?')
        print("tmp_index=",tmp_index)
        if len(tmp_index) == 1:
            next_node_index = int(tmp_index[0])
        elif len(tmp_index) == 2:
            if score >=0 :
                next_node_index = int(tmp_index[0])
            else :
                next_node_index = int(tmp_index[1])
            print("next_node=", next_node_index)
        elif len(tmp_index) == 2:
            if score >= SENTIMENT_THRETHOLD :
                next_node_index = int(tmp_index[0])
            elif score <= -1*SENTIMENT_THRETHOLD :
                next_node_index = int(tmp_index[2])
            else :
                next_node_index = int(tmp_index[1])

    else :
        next_node_index = int(node['next_node'])

    return next_node_index


def exec_scenario(scenario):
    #ヒアリング時のbehaviorの設定
    #behav = Behavior("../dat/scene.csv")
    behav = Behavior(scenario)


    index = 0
    #behaviorがあるまで実行
    while(True) :
        node = behav.get_node(index)
        if node is None:
            logging.info('end senario')
            break

        index = exec_behavior_node(node)
        if index == -1:
            logging.info('end senario')
            break

        #return

    #behaviorに従った動作の実行

def recognize() :
    """
    for i in range(100):
        print(i)
        time.sleep(1)
    """

    text = gclient.recognize(language_code=glanguage,hint_phrases=hists)
    return text

def locale_language():
    language, _ = locale.getdefaultlocale()
    return language

#カメラの初期化
def init_camera() :
    global gcamera
    gcamera = picamera.PiCamera()
    gcamera.resolution = (1200, 700)
    #gcamera.rotation=90

if __name__ == '__main__':

    #引数の確認
    args = sys.argv

    #引数がなければ、デフォルトモード
    argnum = len(args)
    if argnum >= 2 :
        gmode = args[1]

    print("gmode=",gmode)

    #ログの初期化
    logging.basicConfig(level=logging.DEBUG)

    #グローバル変数の初期化
    gclient = CloudSpeechClient()
    gboard = Board()
    glanguage = locale_language()
    #text = client.recognize(language_code=args.language,
    #                        hint_phrases=hints)
    gled_lockfile =fasteners.InterProcessLock(LED_LOCK_FILE)
    gserv_lockfile =fasteners.InterProcessLock(SERV_LOCK_FILE)
    init_camera()

    while(True) :
        #シナリオごとの初期化処理
        #前に聞いた文字列をクリアする。
        gpre_text = ""

        #待ち状態
        print("start listening")
        hists = "パペート, ぱぺーと"
        text = None
        #text = gclient.recognize(language_code=glanguage,hint_phrases=hists)
        text = recognize()

        if text is None:
            logging.info('You said nothing.')
            continue

        logging.info('You said: "%s"' % text)
        listen_say_text(text)
        #テキストをカタカナに変換

        ktext = jaconv.hira2kata(text)
        print("katakana=", ktext)

        #挨拶
        retxt = re.findall('パペット|パペート|^パ(\S+)ト$|コンニチ', ktext)
        if len(retxt) > 0 :
            print("exec hello")
            exec_scenario("../dat/hello.csv")
            continue

        #注文
        retxt = re.findall('注文|オーダー', ktext)
        if len(retxt) > 0 :
            print("exec chuumon")
            exec_scenario("../dat/chuumon.csv")
            continue

        #アンケート
        retxt = re.findall('ゴチソウ', ktext)
        if len(retxt) > 0 :
            print("exec survey")
            exec_scenario("../dat/kansou.csv")
            continue

        #バイバイ
        retxt = re.findall('バイバイ|マタネ|さようなら', ktext)
        if len(retxt) > 0 :
            print("exec baibai")
            exec_scenario("../dat/baibai.csv")
            continue

        #クリア
        retxt = re.findall('クリア', ktext)
        if len(retxt) > 0 :
            monitor_clear()
            continue

        #写真
        retxt = re.findall('シャシン|写真|チーズ', ktext)
        print("写真")
        if len(retxt) > 0 :
            print("写真2")

            exec_picture()
            continue


        #指定されたモードごとの動作を行う
        #if gmode == BehaviorMode.SURVEY :
        #    exec_survey()

    print("end papeet_main")
