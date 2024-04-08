import time
import cv2
import matplotlib.pyplot as plt
import mediapipe as mp
from dasbus.connection import SessionMessageBus


bus = SessionMessageBus()
proxy = bus.get_proxy("org.newm.Gestures", "/org/newm/Gestures")

def new_gesture():
    res = proxy.New("swipe-3")
    if res != "":
        return bus.get_proxy("org.newm.Gestures.Gesture", res)
    else:
        return None

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

OUTPUT = False
OUTPUT = True

try:
    with mp.solutions.hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5, max_num_hands=1) as hands:

        current = None
        init_counter = 0
        init = 0., 0.

        counter = 0
        while cap.isOpened():
            ret, frame = cap.read()

            # Hacky: Drop some frames to keep latency down
            counter += 1
            if counter%2 == 0:
                continue

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            t = time.time()
            results = hands.process(frame_rgb)
            dt = time.time() - t

            # print("dt=%f" % dt)
            if results.multi_hand_landmarks is not None:
                for hand_landmarks in results.multi_hand_landmarks:
                    index = [
                        hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_MCP],
                        hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_PIP],
                        hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP],
                    ]
                    index = [(l.x, l.y) for l in index]
                    scalar = (index[2][0] - index[1][0]) * (index[1][0] - index[0][0]) + (index[2][1] - index[1][1]) * (index[1][1] - index[0][1])
                    print(scalar)

                    if scalar > 0:
                        init_counter += 1
                        if init_counter > 2:
                            if current is None:
                                current = new_gesture()
                                print("New")
                                init = index[0]
                            else:
                                print("Update")
                                current.Update(["delta_x", "delta_y"], [- (index[0][0] - init[0]), index[0][1] - init[1]])
                    else:
                        init_counter = 0
                        if current is not None:
                            print("Terminate")
                            current.Terminate()
                            current = None

                if OUTPUT:
                    mp.solutions.drawing_utils.draw_landmarks(frame, hand_landmarks, mp.solutions.holistic.HAND_CONNECTIONS)
            else:
                init_counter = 0
                if current is not None:
                    print("Terminate")
                    current.Terminate()
                    current = None
            
            if OUTPUT:
                cv2.imshow('Preview', frame)

finally:
    cap.release()
    cv2.destroyAllWindows()
