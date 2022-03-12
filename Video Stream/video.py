from flask import Flask, render_template, Response, request
import requests
from flask_cors import CORS
import cv2
import os
import platform
import json
import base64
import time
import glob
import socket

class VideoCamera(object):
    def __init__(self, ip):
        # 通過opencv獲取實時影片流
        self.video = cv2.VideoCapture("rtsp://" + ip + ":8554/unicast")
        # 修改串流格式H264格式
        self.video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
        # self.video.set(cv2.CAP_PROP_FPS, 30)
        # print(self.video.get(5))
    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        # 因為opencv讀取的圖片並非jpeg格式，因此要用motion JPEG模式需要先將圖片轉碼成jpg格式圖片
        isOpened = self.video.isOpened()

        if isOpened :
            ret, jpeg = cv2.imencode('.jpeg', image)
            return jpeg.tobytes()
        else :
            return None

    def get_isOpened(self):
        return self.video.isOpened()

app = Flask(__name__)
# r route 名稱
# origins 域名 或 ip ,隔開
CORS(app, resources={r"/.*": {"origins": "*"}})

def gen(camera):
    while True:
        frame = camera.get_frame()
        # 使用generator函式輸出影片流， 每次請求輸出的content型別是image/jpeg
        yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def check_isOpened(camera):
    check = camera.get_isOpened()
    return check

# def get_fps(camera):
#     return camera.get_fps()

    # 判斷ip是否連通
def decide_server(ip):
    sys = platform.system()
    if sys == "Windows":
        # -n 1 ping的次數
        visit_ip = os.popen('ping %s -n 1' % ip)
        result = visit_ip.read()
        visit_ip.close()
        if 'TTL' in result:
            return True
        else:
            return False
    elif sys == "Linux":
        visit_ip = os.popen('ping -c 1 %s' % ip)
        result = visit_ip.read()
        visit_ip.close()
        if 'ttl' in result:
            return True
        else:
            return False
    else:
        print("Error")
        return False

def get_img_list(ip, frame_num):
        video = cv2.VideoCapture("rtsp://" + ip + ":8554/unicast")
        # 修改串流格式H264格式
        video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
        # 
        quantity = 1
        timeF = int(frame_num)
        # i = 0
        img_list = list()
        rval,frame = video.read()
        fps = 0

        if rval:
            start = video.get(cv2.CAP_PROP_POS_MSEC)
            img_list.append(cv2_base64(frame))
            # img_list.append("data:image/png;base64," + cv2_base64(frame))

            while quantity < timeF:
                # i = i + 1
                rval,frame = video.read()
                # 劉覽器才會顯示
                # img_list.append("data:image/png;base64," + cv2_base64(frame))
                img_list.append(cv2_base64(frame))
                # 存檔
                # cv2.imwrite('C:/laravel/python/images/'+str(quantity)+'.jpg',frame)
                quantity = quantity + 1
                # print(img_list)
            end = video.get(cv2.CAP_PROP_POS_MSEC)
            # 計算每秒幀數
            fps = 1000/((end - start)/timeF)

        video.release()

        return {'fps': "{:.1f}".format(fps), 'img_list': img_list}

def cv2_base64(image):
    base64_str = cv2.imencode('.png',image)[1].tobytes()
    # base64_str = base64.b64encode(base64_str).decode()
    base64_str = base64.b64encode(base64_str)
    return base64_str

def image_b64_Encode(imgPath): 
    im_b64 = None
    with open(imgPath, 'rb') as f:
        im_b64 = base64.b64encode(f.read())
    return im_b64


def image_b64_Decode(im_b64):
    im_binary = base64.b64decode(im_b64)
    buf = io.BytesIO(im_binary)
    img = Image.open(buf)
    #img.show()
    #cv2.imshow('imageDecode',img)

@app.route('/video_feed', methods=['GET'])  # 這個地址返回影片流響應
def video_feed():
    ip = request.args.get('ip');
    return Response(gen(VideoCamera(ip)),mimetype='multipart/x-mixed-replace; boundary=frame')
    # ip = request.args.get('ip');
    # check = check_isOpened(VideoCamera(ip))
    # print(check)
    # if check :
    #     return Response(gen(VideoCamera(ip)),mimetype='multipart/x-mixed-replace; boundary=frame')
    # else :
    #     return json.dumps({'check': None})
        

@app.route('/ip_check', methods=['GET'])  # 這個地址返回影片流響應
def ip_check():
    ip = request.args.get('ip');
    # check = cv2.VideoCapture("rtsp://" + ip + ":8554/unicast").isOpened()
    check = decide_server(ip)
    return json.dumps({'check': check})


@app.route('/video_information', methods=['POST'])  # 這個地址返回影片流響應
def video_information():
    # ip = request.args.get('ip');

    ip = request.form.get('ip');
    
    

    bw_shift = request.form.get('bw_shift')
    pix2mm_ratio =request.form.get('pix2mm_ratio')
    count_shift = request.form.get('count_shift')
    frame_num = request.form.get('frame_num')
    company_name = request.form.get('company_name')
    device_name = request.form.get('device_name')
    date = request.form.get('date')
    imgData = get_img_list(ip, frame_num)

    payload = {
        'bw_shift': bw_shift, 
        'pix2mm_ratio': pix2mm_ratio, 
        'count_shift': count_shift,
        'frame_num': frame_num,
        'company_name': company_name, 
        'device_name' : device_name,
        'date': date, 
        # 'img_list': json.loads(imgData)['img_list']
        'img_list': imgData['img_list']
        # 'img_list': img_b64_list
    }

    r = requests.post('http://10.1.3.183:5000/PostImagePC', data = payload)
    # print(json.loads(r.text))

    # return imgData
    return json.dumps({'fps': imgData['fps'], 'msg': json.loads(r.text)})

if __name__ == '__main__':
    app.run(host=socket.gethostbyname(socket.gethostname()), port=8000)
