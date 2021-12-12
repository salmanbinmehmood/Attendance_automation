from flask import Flask,render_template,Response,request,redirect
import cv2
from pyzbar.pyzbar import decode
import numpy as np
from qrcode import QRCode
import qrcode

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

import os 
import time





app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///student_data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)

username='admin'
password='admin'

file_name=''
path=os.environ['USERPROFILE']
path=os.path.join(path,file_name)
submission_successful=True
authentication=False

class Attendance(db.Model):
    sn=db.Column(db.Integer,primary_key=True)
    id=db.Column(db.Integer,nullable=False)
    name=db.Column(db.String(200),nullable=False)
    date=db.Column(db.DateTime,default=datetime.utcnow)
    def __repr__(self) -> str:
        return f"{self.sn}-{self.id}-{self.name}"



class AddingData(db.Model):
    qr_id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(200),nullable=False)
    date=db.Column(db.DateTime,default=datetime.utcnow)
    def __repr__(self) -> str:
        return f"{self.qr_id}-{self.name}"


cap=cv2.VideoCapture(0)
def generate_frames():
    while True:
        success,frame=cap.read()
        if not success:
            break
        else:
            for qrcode in decode(frame):
                print(qrcode.data.decode('utf-8'))
                DATA=qrcode.data.decode('utf-8')
                points=np.array([qrcode.polygon],np.int32)
                points=points.reshape((-1,1,2))
                cv2.polylines(frame,[points],True,(255,0,255),5)
                if db.session.query(AddingData.qr_id).filter_by(qr_id=int(DATA)).first():
                    
                    std_name, = db.session.query(AddingData.name).filter_by(qr_id=int(DATA)).first()
                    std_id=db.session.query(AddingData.qr_id).filter_by(qr_id=int(DATA)).first()
                    print('exist')
                    print(type(std_name))
                    print(std_name)
                    
                    # print(type(id))
                    std_id=std_id[0]
                    print(std_id)  
                    print(type(std_id))
                    id=std_id
                    name=std_name
                    attendace=Attendance(id=id,name=name)
                    db.session.add(attendace)
                    db.session.commit()
                    time.sleep(1)
                # attendaceDetails=Attendance.query.all()
                # print(DATA)



            ret,buffer=cv2.imencode('.jpg',frame)
            
        
        frame2=buffer.tobytes()
        
        
                
        
        
        yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame2 + b'\r\n')
    cv2.waitKey(1)
    cv2.destroyAllWindows()
@app.route("/")
def hello_world():
    global authentication
    authentication=False
    return render_template('index.html')

@app.route("/video")
def video():
    global authentication
    authentication=False
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/login',methods=['POST','GET'])
def login():
    global submission_successful
    global authentication
    authentication=False
    submission_successful = True
    
    return render_template('login.html',submission_successful=submission_successful)


@app.route('/admin',methods=['POST','GET'])
def admin():
    global submission_successful
    global authentication
    
    username=request.form['username']
    password=request.form['password']
    if username=='admin' and password=='admin':
        
        attendaceDetails=Attendance.query.all()
        authentication=True
        
        return render_template('admin.html',attendaceDetails=attendaceDetails)
    else:
        submission_successful = False
    
       
        return render_template('login.html',submission_successful=submission_successful)
   


@app.route('/data',methods=['POST','GET'])
def DisplayData():
    global authentication
    if authentication:
        if request.method=='POST':

            name=request.form['name']
            add_data=AddingData(name=name)
            db.session.add(add_data)
            db.session.commit()
            qid=db.session.query(AddingData.qr_id).order_by(AddingData.qr_id.desc()).first()

            qr=QRCode(version=8,
            box_size=5,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            border=3)

            qid=qid[0]

            dt=qr.add_data(data=qid)
            
            qr.make(dt)
        
            img=qr.make_image(fill='black',back='white')
            rows=db.session.query(AddingData).count()
            img.save(f'qrcode{rows}.png')
        allDetails=AddingData.query.all()
    
        return render_template('data.html',allDetails=allDetails)

@app.route("/delete/<int:qr_id>")
def delete(qr_id):
    data=AddingData.query.filter_by(qr_id=qr_id).first()
    db.session.delete(data)
    db.session.commit()
    return redirect('/data')



if __name__=="__main__":
    app.run(debug=True)
