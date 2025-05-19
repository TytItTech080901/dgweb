import cv2
import time
from ultralytics import YOLO
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

class Detector:
    def __init__(self, TPEs = 4, model_path = "Yolo/best6_rknn_model", camera_id = 1, show_img = False):
        """
        实例化目标检测器

        Args:
            TPEs (int): 线程池的线程数
            model_path (str): 模型路径
            camera_id (int): 摄像头ID
            show_img (bool): 是否显示图像
        """

        self.TPEs = TPEs
        self.model_path = model_path
        self.camera_id = camera_id
        self.show_img = show_img
        self.running = False
        self.fps = 0
        self.frames = 0
        self.position = [0.0, 0.0]
        self.width = 0.0
        self.height = 0.0
        self.confidence = 0.0
        self.detected = False

    def initialize(self):
        """初始化检测器资源：摄像头和线程池"""
        # 初始化模型池
        self.pool = rknnPoolExecutor(
            model_path=self.model_path, 
            TPEs=self.TPEs, 
            func=thread_safe_predict
        )

        # 初始化相机
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise IOError("无法打开摄像头")

        # 初始化异步处理帧
        if self.cap.isOpened():
            for i in range(self.TPEs + 1):
                ret, frame = self.cap.read()
                if not ret:
                    self.cap.release()
                    del self.pool
                    exit(-1)
                self.pool.put(frame)
        
        return True
    
    def process_frame(self):
        """处理帧数据"""
        if not self.cap or not self.cap.isOpened():
            return False
        
        ret, frame = self.cap.read()
        if not ret:
            return False
        
        self.pool.put(frame)

        results, flag = self.pool.get()
        if not flag:
            return False
        
        # 重置检测状态
        self.detected = False

        for result in results:
            boxes = result.boxes
            if len(boxes) > 0:
                # 找出置信度最高的框
                box_best = max(boxes, key=lambda box: box.conf[0].cpu().numpy())
                
                # 获取归一化坐标、宽高
                self.position[0], self.position[1], self.width, self.height = box_best.xywhn[0].cpu().numpy()
                
                # 转换为相对于中心的坐标
                self.position[0] -= 0.5
                self.position[1] -= 0.5
                
                # 记录置信度
                self.confidence = float(box_best.conf[0].cpu().numpy())
                self.detected = True
            else:
                # 未检测到目标
                self.position[0] = 0.0
                self.position[1] = 0.0
                self.width = 0.0
                self.height = 0.0
                self.confidence = 0.0
                self.detected = False
            if self.show_img:
                self._display_frame(frame, boxes, result)
        
        self.frames += 1

        return True
    
    def _display_frame(self, frame, boxes, result):
        """在图像上显示检测结果"""
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            confidence = box.conf[0].cpu().numpy()
            class_id = int(box.cls[0].cpu().numpy())
            class_name = "book"  # 默认类别名称
            
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
        cv2.putText(
            frame,
            str(int(self.fps)),
            (7, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            3,
            (100, 255, 0),
            3,
            cv2.LINE_AA,
        )
        
        # 显示图像
        cv2.imshow("Object Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return True
        
        return True

    def start(self):
        """启动检测循环"""
        if self.running:
            return False
            
        if not self.cap or not self.pool:
            self.initialize()
            
        self.running = True
        self.detection_thread = Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        return True

    def _detection_loop(self):
        """检测主循环，在单独线程中运行"""
        loopTime = time.time()
        initTime = time.time()
        
        while self.running and self.cap and self.cap.isOpened():
            if not self.process_frame():
                break
                
            # 每30帧更新一次FPS
            if self.frames % 30 == 0:
                self.fps = 30 / (time.time() - loopTime)
                loopTime = time.time()
                
        print(f"检测结束，平均帧率: {self.frames / (time.time() - initTime):.2f} FPS")

    def stop(self):
        """停止检测循环"""
        self.running = False
        if hasattr(self, 'detection_thread'):
            self.detection_thread.join(timeout=1.0)
        self.cleanup()
        
    def cleanup(self):
        """清理资源"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
    def get_position(self):
        """获取当前检测到的目标位置信息"""
        return {
            "detected": self.detected,
            "x": self.position[0],
            "y": self.position[1],
            "w": self.width,
            "h": self.height,
            "confidence": self.confidence,
        }
        
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.cleanup()

def main():
        # 1. 创建Detector实例
    # 参数说明:
    # TPEs: 线程池大小，默认4
    # model_path: 模型文件路径，默认"Yolo/best6_rknn_model"
    # camera_id: 摄像头ID，默认1
    # show_img: 是否显示检测结果，默认False
    detector = Detector(
        TPEs=4,
        model_path="Yolo/best6_rknn_model",
        camera_id=1,
        show_img=False  # 设置为True可以看到检测效果
    )
    
    # 2. 初始化检测器
    detector.initialize()
    
    # 3. 启动检测循环
    detector.start()
    
    try:
        # 4. 使用检测结果
        for _ in range(1000):  # 循环100次
            # 获取当前检测到的目标位置信息
            position_info = detector.get_position()
            
            # 输出检测结果
            if position_info["detected"]:
                print(f"检测到目标: 位置 x={position_info['x']:.2f}, y={position_info['y']:.2f}, 置信度={position_info['confidence']:.2f}")
                
            # 每隔0.1秒获取一次检测结果
            time.sleep(0.1)
    finally:
        # 5. 停止检测并释放资源
        detector.stop()
    


if __name__ == "__main__":
    # 运行主函数
    main()
