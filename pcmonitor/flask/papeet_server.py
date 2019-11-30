from flask import Flask, request, jsonify
import json
import fasteners

CMD_REQ='../data/cmd_req.json'
MAX_CHARA_LEN = 12
LOCK_FILE = '/tmp/papeet_lockfile'

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # JSONでの日本語文字化け対策
glockfile =fasteners.InterProcessLock(LOCK_FILE)


@app.route('/', methods=['POST'])
def post_json():
    d = request.get_json()  # POSTされたJSONを取得
    #JSONのファイル出力
    #d={'PATTERN':int(LEDPattern.WIPE), 'COLOR':(255, 255, 0), 'CNTRL':int(LEDCntrl.START), 'TIME':10}
    print(d)
    #gled_lockfile.acquire()
    glockfile.acquire()
    with open(CMD_REQ, 'w') as f:
        json.dump(d, f, indent=4, ensure_ascii=False)
    glockfile.release()

    return jsonify(d)  # JSONをレスポンス

@app.route('/', methods=['GET'])
def get_json_from_dictionary():
    dic = {
        'foo': 'bar',
        'ほげ': 'ふが'
    }
    return jsonify(dic)  # JSONをレスポンス

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
