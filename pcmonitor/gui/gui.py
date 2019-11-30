import wx
import time
import json
import pprint
import os
import fasteners
from enum import IntEnum

class CMDType(IntEnum):
    NONE = 0
    TEXT_SAY = 1
    TEXT_LISTEN = 2
    IMG_BILL = 3

CMD_REQ='../data/cmd_req.json'
MAX_CHARA_LEN = 12
LOCK_FILE = '/tmp/papeet_lockfile'

class MyApp(wx.Frame):
    def __init__(self, parent, title):
        self.lockfile =fasteners.InterProcessLock(LOCK_FILE)

        wx.Frame.__init__(self, parent, title=title, size=(1200, 700), pos=(0, 20))
        self.main_panel = wx.Panel(self)

        date_time = wx.DateTime.Now()
        self.label_1 = wx.StaticText(self.main_panel, label="Say test", pos=(20, 30))
        #self.label_2 = wx.StaticText(self.main_panel, label=time.strftime('%d/%m/%Y %H:%M'), pos=(20,50))
        self.label_2 = wx.StaticText(self.main_panel, label="Listen test", pos=(20,self.GetSize()[1]-270))

        #フォント設定
        font = wx.Font(100, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.label_1.SetFont(font)
        self.label_2.SetFont(font)

        #クリアボタン
        self.button_1 = wx.Button(self.main_panel, label='clear', pos=(self.GetSize()[0]/2, 5))
        self.button_1.Bind(wx.EVT_BUTTON, self.click_button_1)

        #画像の準備
        self.PhotoMaxSize = self.GetSize()[0]-100
        img = wx.EmptyImage(240,240)
        #self.imageCtrl = wx.StaticBitmap(self.main_panel,bitmap=wx.BitmapFromImage(img))
        #self.imageCtrl = wx.StaticBitmap(self.main_panel, pos=(self.GetSize()[0]/2, 30))
        self.imageCtrl = wx.StaticBitmap(self.main_panel)


        # wx.Timerを追加し、update() を１秒間隔で呼び出す
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update)
        self.timer.Start(200) # とりあえず１秒(1000ms) 間隔

        self.Show()

    #画面のクリア処理
    def click_button_1(self, event):
        self.clear_all()

    def exec_cmd_say(self, text):
        #テキストが長い場合には、改行を入れる
        l = len(text)
        if l > MAX_CHARA_LEN :
            text1 = text[:MAX_CHARA_LEN]
            text2 = text[MAX_CHARA_LEN:]
            text = text1 + '\n' + text2
        self.label_1.SetLabel(text)

    def exec_cmd_listen(self, text):
        #テキストが長い場合には、改行を入れる
        l = len(text)
        if l > MAX_CHARA_LEN :
            text1 = text[:MAX_CHARA_LEN]
            text2 = text[MAX_CHARA_LEN:]
            text = text1 + '\n' + text2
        self.label_2.SetLabel(text)


    def exec_cmd_img(self, text):
        filepath = text
        #img = wx.Image(filepath, wx.BITMAP_TYPE_ANY)
        img = wx.Image(filepath)
        # scale the image, preserving the aspect ratio
        W = img.GetWidth()
        H = img.GetHeight()
        if W > H:
            NewW = self.PhotoMaxSize
            NewH = self.PhotoMaxSize * H / W
        else:
            NewH = self.PhotoMaxSize
            NewW = self.PhotoMaxSize * W / H
        img = img.Scale(NewW,NewH)

        self.imageCtrl.SetBitmap(wx.BitmapFromImage(img))
        posx= (self.GetSize()[0]-NewW)/2
        #画面のオフセットを算出する
        self.imageCtrl.SetPosition((posx ,25))
        self.imageCtrl.Show(True)
        #self.main_panel.Refresh()

    def clear_all(self) :
        self.label_1.SetLabel("")
        self.label_2.SetLabel("")
        self.imageCtrl.Show(False)


    # 1秒間隔で呼ばれる関数
    def update(self, event):
        #jsonファイルの内容を確認する
        if os.path.exists(CMD_REQ) == True :
            with open(CMD_REQ) as f:
                d = json.load(f)
                pprint.pprint(d, width=40)
                self.lockfile.acquire()
                os.remove(CMD_REQ)
                self.lockfile.release()
            #画面クリア
            self.clear_all()
            type = int(d['TYPE'])
            #コマンド毎の処理の実行
            if type == CMDType.TEXT_SAY:
                print("say")
                self.exec_cmd_say(d['TEXT'])

            elif type == CMDType.TEXT_LISTEN:
                print("say")
                self.exec_cmd_listen(d['TEXT'])

            elif type == CMDType.IMG_BILL:
                print("img")
                self.exec_cmd_img(d['IMG'])

app = wx.App(False)
frame = MyApp(None, "MyApp")
app.MainLoop()
