import fasteners
import json
import sys
import fasteners
from time import sleep
from papeet_def import *
SERV_REQ_FILE='../dat/serv_req.json' #SERVリクエストファイル
LOCK_FILE = '/tmp/lockfile_serv'

SLEEP_SAMPLING_TIME = 0.5

def touch(path):
    if os.path.isfile(path):
        pass
    else:
        with open(path, "w", encoding="UTF-8") as f:
            pass

def save_serv_reqfile(d) :
    glock.acquire()
    with open(SERV_REQ_FILE, 'w') as f:
        json.dump(d, f, indent=4)
    glock.release()

if __name__ == '__main__':

    glock = fasteners.InterProcessLock(LOCK_FILE)

    #キー入力を監視する
    while(True):
        print("please input, r:after wait restart, bs:body swing, bss:body swing small, br:body right, brs: body right small, bls:body left small, bl body left, bc: body center, hc: head center, hu: head up, hd head down")
        key = input()
        if key == 'r':
            print('r is selected')
            touch('../dat/restart')

        elif key == 'bs':
            print('bs is selected')
            d={'PATTERN':int(ServPattern.BODY_SWING), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)

        elif key == 'bss':
            print('bss is selected')
            d={'PATTERN':int(ServPattern.BODY_SWING_SMALL), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)
            sleep(1)
            save_serv_reqfile(d)
            sleep(1)
            save_serv_reqfile(d)


        elif key == 'br':
            print('br is selected')
            d={'PATTERN':int(ServPattern.BODY_RIGHT ), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)

        elif key == 'brs':
            print('brs is selected')
            d={'PATTERN':int(ServPattern.BODY_RIGHT_SMALL ), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)

        elif key == 'bl':
            print('bl is selected')
            d={'PATTERN':int(ServPattern.BODY_LEFT ), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)

        elif key == 'bls':
            print('bls is selected')
            d={'PATTERN':int(ServPattern.BODY_LEFT_SMALL ), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)

        elif key == 'bc':
            print('bc is selected')
            d={'PATTERN':int(ServPattern.BODY_CENTER ), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)

        elif key == 'hc':
            print('hc is selected')
            d={'PATTERN':int(ServPattern.HEAD_CENTER ), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)

        elif key == 'hu':
            print('hu is selected')
            d={'PATTERN':int(ServPattern.HEAD_UP ), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)

        elif key == 'hd':
            print('hd is selected')
            d={'PATTERN':int(ServPattern.HEAD_DOWN ), 'CNTRL':int(LEDCntrl.START), 'TIME':1}
            save_serv_reqfile(d)
