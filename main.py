from flask import Flask, render_template, request
import os
import cv2
import numpy as np
import urllib
import queueing

app = Flask(__name__)

@app.route('/')
def view_form():
    return render_template("main_page.html")

@app.route('/read_from_disk', methods=['GET'])
def read_from_disk():
    try:
        save_to_disk = request.args.get("save") is not None
        path = request.args.get("path")
        path = os.path.join("images",path)
        img = cv2.imread(path)
        if img is None or path is None:
            return f"Couldn't read file from disk"
        task = queueing.Task(img, save_to_disk)
        return str(task.id)
    except Exception as ex:
        return f"Couldn't read file from disk<br>Reason: {ex}"
    
@app.route('/read_multiple_from_disk', methods=['GET'])
def read_multiple_from_disk():
    try:
        save_to_disk = request.args.get("save") is not None
        count = int(request.args.get("count") or "1")
        path = request.args.get("path")
        path = os.path.join("images",path)
        img = cv2.imread(path)
        if img is None or path is None:
            return f"Couldn't read file from disk"
        task_ids = []
        for _ in range(count):
            task_ids.append(queueing.Task(img, save_to_disk).id)
        return str(task_ids)
    except Exception as ex:
        return f"Couldn't read file from disk<br>Reason: {ex}"

@app.route('/read_from_url', methods=['GET'])
def read_from_url():
    try:
        save_to_disk = request.args.get("save") is not None
        url = request.args.get("url")
        req = urllib.request.urlopen(url)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        if img is None:
            return f"Couldn't read file from url"
        task = queueing.Task(img, save_to_disk)
        return str(task.id)
    except Exception as ex:
        return f"Couldn't read URL, Reason: {ex}"
    

@app.route('/send_image', methods=['POST'])
def send_image():
    try:
        image_file = request.files['image']
        save_to_disk = 'save' in request.form
        arr = np.asarray(bytearray(image_file.stream.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        if img is None:
            return f"Couldn't send image"
        task = queueing.Task(img, save_to_disk)
        return str(task.id)
    except Exception as ex:
        return f"Couldn't send image, Reason: {ex}"

@app.route('/verify_status', methods=['GET'])
def verify_status():
    try:
        id = int(request.args.get("id"))
        if id > len(queueing.tasks):
            return "Invalid task id"
        else:
            if not hasattr(queueing.tasks[id-1], 'result'):
                return "Task incomplete"
            result = queueing.tasks[id-1].result
            if result:
                return f"Task complete, people count: {result}"
            else:
                return "Task incomplete"
                
    except Exception as ex:
        return f"Couldn't process request, Reason: {ex}"

if __name__ == "__main__":
    queueing.initialize_queueing()
    app.run()