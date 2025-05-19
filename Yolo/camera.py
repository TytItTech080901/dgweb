import cv2
import time
from ultralytics import YOLO
# from rknn.api import RKNN
from threading import Thread
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

SHOW_IMG = False

class rknnPoolExecutor:
    def __init__(self, model_path, TPEs, func):
        self.TPEs = TPEs
        self.queue = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=TPEs)
        self.models = self.__init_models(model_path, TPEs)
        self.func = func
        self.num = 0

    def put(self, frame):
        self.queue.put(
            self.pool.submit(self.func, self.models[self.num % self.TPEs], frame)
        )
        self.num += 1

    def get(self):
        if self.queue.empty():
            return None, False
        temp = []
        temp.append(self.queue.get())
        for frame in as_completed(temp):
            return frame.result(), True

    def __init_models(self, model_path, TPEs):
        rknn_list = []
        for i in range(TPEs):
            rknn_list.append(YOLO(model_path))
        return rknn_list


def thread_safe_predict(model, frame):
    outputs = model(frame, verbose=False)
    return outputs


def main():
    TPEs = 4
    model_path = "Yolo/best6_rknn_model"
    pool = rknnPoolExecutor(model_path=model_path, TPEs=TPEs, func=thread_safe_predict)

    # 打开默认摄像头
    cap = cv2.VideoCapture(1)  # 0 是默认摄像头，1 是外接摄像头
    if not cap.isOpened():
        raise IOError("无法打开摄像头")

    # 初始化异步所需要的帧
    if cap.isOpened():
        for i in range(TPEs + 1):
            ret, frame = cap.read()
            if not ret:
                cap.release()
                del pool
                exit(-1)
            pool.put(frame)

    fps, frames, loopTime, initTime = 0, 0, time.time(), time.time()
    while cap.isOpened():
        position = [0.0, 0.0]
        frames += 1
        ret, frame = cap.read()
        if not ret:
            break
        pool.put(frame)
        results, flag = pool.get()
        if flag == False:
            break
        # 在图像上绘制检测结果
        for result in results:
            boxes = result.boxes
            if(len(boxes) > 0):
                box_best = max(boxes, key=lambda box: box.conf[0].cpu().numpy())
                position[0], position[1], width, height = box_best.xywhn[0].cpu().numpy()
                position[0] -= 0.5
                position[1] -= 0.5
                print(f"检测到物体: 位置 = ({position[0]:.3f}, {position[1]:.3f})")
            else:
                position[0] = 0.0
                position[1] = 0.0
                print(f"未检测到物体: 位置 = ({position[0]:.3f}, {position[1]:.3f}))")

            if SHOW_IMG:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = "book"

                    if box.conf[0].cpu().numpy() > box_best.conf[0].cpu().numpy():
                        box_best = box
                        label = f"{class_name} {confidence:.2f}"
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(
                            frame,
                            label,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.9,
                            (0, 255, 0),
                            2,
                        )
                # 显示帧率

        if SHOW_IMG:
            cv2.putText(
                frame,
                str(int(fps)),
                (7, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                3,
                (100, 255, 0),
                3,
                cv2.LINE_AA,
            )
            cv2.imshow("test", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        if frames % 30 == 0:
            fps = 30 / (time.time() - loopTime)
            # print("30帧平均帧率:\t", fps, "帧")
            loopTime = time.time()

    print("总平均帧率\t", frames / (time.time() - initTime))
    # 释放cap和rknn线程池
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # 运行主函数
    main()
