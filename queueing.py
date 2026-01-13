import cv2
from queue import Queue
from threading import Thread
import os
import datetime
import person_detection

queue_thread_count = 4

queue_threads = []

task_queue = Queue()

tasks = []

image_path = os.path.join("images","none")

def queue_thread_loop(id):
    global task_queue,image_path
    while True:
        try:
            current_task = task_queue.get()
            print(f"Thread {id}: Queued task id {current_task.id}")
            results = person_detection.detect_people(current_task.image)
            current_task.result = results[0]
            print(f"Thread {id}: Task id {current_task.id} finished with result {current_task.result}")
            if current_task.save_to_disk:
                cv2.imwrite(os.path.join(image_path, f"{current_task.id}.png"), results[1])
            del current_task.image # Free the RAM used by the image
        except Exception as ex:
            print(ex)
            continue


class Task():
    def __init__(self, image, save_to_disk):
        global tasks, task_queue
        tasks.append(self)
        self.id = len(tasks)
        self.image = image
        self.save_to_disk = save_to_disk
        task_queue.put(self)
        task_queue.task_done()


def initialize_queueing():
    global tasks,queue_threads,task_queue,image_path
    tasks = []
    queue_threads = []
    task_queue = Queue()
    image_folder = "{date:%Y-%m-%d_%H-%M-%S}".format(date=datetime.datetime.now())
    image_path = os.path.join("images","saved",image_folder)
    if not os.path.exists(image_path):
        os.makedirs(image_path)
    for i in range(queue_thread_count):
        thread = Thread(target=queue_thread_loop, args=(i,))
        thread.setDaemon(True)
        queue_threads.append(thread)
        thread.start()
