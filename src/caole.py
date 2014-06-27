from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
import time
import base64,hmac,hashlib
#from flask import redirect
#from flask import request
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError





def __init__(self):
    self.count=0

class Info:
    userlist =[]
    count =0
    msglist =[]
    MAX_COUNT=51
    def __init__(self,seqno,user,time,msg):
        self.seqno = seqno
        self.user = user
        self.time = time
        self.msg = msg

    def serialize(self):
        return {
            'seqno':self.seqno,
            'user':self.user,
            'time':self.time,
            'msg':self.msg
        }

class MessageServer(object):

    def __init__(self):
        self.observers = []

    def add_message(self, msg):
        for ws in self.observers:
            try:
                ws.send(msg)
            except WebSocketError:
                self.observers.pop(self.observers.index(ws))
                print ws, 'is closed'
                continue

msgsrv = MessageServer()
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/websock')
def websock():
    return render_template('websock.html')

@app.route('/message/')
def message():
    ws = request.environ['wsgi.websocket']
    handws(ws)   

def handws(ws):
    while True:
        message = ws.receive()
        if message is None:
            break
        ws.send(message)


@app.route('/fileupload')
def uploads():
    policy_document ='{"expiration": "2014-06-01T00:00:00Z",\
    "conditions":[{"bucket":"caoyuwei-test"},\
     ["starts-with", "$key", "uploads/"],{"acl":"private"},\
     {"success_action_redirect":"http://localhost/"},\
     ["starts-with", "$Content-Type", ""],\
     ["content-length-range", 0, 1048576]]}'    
    key = "AKIAJYWBX4CM465TRCAQ"
    pwd = "ZRkb1/g/gvAxT46AoRtzqeqAAi+KI+SqhcBqGwzH"
    print "pwd: ",pwd
    policy = base64.b64encode(policy_document)
    print "key: ",key
    signature = base64.b64encode(hmac.new(pwd, policy, hashlib.sha1).digest())
    print "policy: ",policy
    print "signature: ",signature
    return render_template('fileupload.html',policy=policy,sig=signature,key=key)    

@app.route('/cc/login', methods=['POST'])
def login():
    name = request.form['name']
    try:
        Info.userlist.index(name)
        appendMsg("<font color='red'>" + name+" join chat</font>","")        
        return render_template('chat_room.html',name=name)
    except ValueError:
        Info.userlist.append(name)
        return render_template('chat_room.html',name=name)

def appendMsg(user,msg):
    if (Info.MAX_COUNT-1) ==Info.count:
        Info.msglist =[]
        Info.count =0
    times = time.strftime('%H:%M:%S', time.localtime())    
    info = Info(Info.count,user,times,msg)
    Info.msglist.append(info)
    #print "list <<<: ",len(Info.msglist)
    Info.count =Info.count+1

@app.route('/cc/recive', methods=['POST'])
def recive():
    msg = request.form['msg']
    user = request.form['user']
    appendMsg(user,msg)
    return jsonify({'status': "OK", 'result':""})

@app.route('/cc/retry', methods=['POST'])
def retry():
    count = int(request.form['count'])
    if count <0:
        count =0
    elif count > Info.count:
        count =Info.count

    if Info.count == count:
        return jsonify({'status': "NONE", 'result':"NULL"})
    return jsonify(**{'status': "OK", 'result':[e.serialize() for e in Info.msglist[count:]]})       

@app.route('/cc/chat_room')
def chat_room():
    return render_template('chat_room.html',name=None)

@app.route('/static/<path:filename>')
def sfile(filename):
    return send_from_directory('static',filename)






if __name__ == '__main__':
    #app.debug = True
    #app.run(host='192.168.126.108',port=8080)
    http_server = WSGIServer(('',8080), app, handler_class=WebSocketHandler)
    http_server.serve_forever()    
