import cv2
import numpy as np
import time


def video_to_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames


def calculate_optical_flow(prev_frame, next_frame):
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    next_gray = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)

    p0 = cv2.goodFeaturesToTrack(prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30)
    p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, next_gray, p0, None)

    return p0, p1, st


def stabilize_frames(frames):
    stabilized_frames = []
    transforms = []
    for i in range(1, len(frames)):
        p0, p1, st = calculate_optical_flow(frames[i - 1], frames[i])
        good_old = p0[st == 1]
        good_new = p1[st == 1]

        m = cv2.estimateAffinePartial2D(good_old, good_new)[0]
        transforms.append(m)

    for i in range(len(frames)):
        if i == 0:
            stabilized_frames.append(frames[i])
        else:
            stabilized_frame = cv2.warpAffine(frames[i], transforms[i - 1], (frames[i].shape[1], frames[i].shape[0]))
            stabilized_frames.append(stabilized_frame)

    return stabilized_frames


def sharpen_frame(frame):
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    return cv2.filter2D(frame, -1, kernel)


def video_to_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames


def calculate_optical_flow(prev_frame, next_frame):
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    next_gray = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)

    p0 = cv2.goodFeaturesToTrack(prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30)
    p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, next_gray, p0, None)

    return p0, p1, st


def stabilize_frames(frames):
    stabilized_frames = []
    transforms = []
    for i in range(1, len(frames)):
        p0, p1, st = calculate_optical_flow(frames[i - 1], frames[i])
        good_old = p0[st == 1]
        good_new = p1[st == 1]

        m = cv2.estimateAffinePartial2D(good_old, good_new)[0]
        transforms.append(m)

    for i in range(len(frames)):
        if i == 0:
            stabilized_frames.append(frames[i])
        else:
            stabilized_frame = cv2.warpAffine(frames[i], transforms[i - 1], (frames[i].shape[1], frames[i].shape[0]))
            stabilized_frames.append(stabilized_frame)

    return stabilized_frames


def sharpen_frame(frame):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(frame, -1, kernel)


def apply_filters(frame, filter_type):
    if filter_type == "Grayscale":
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    elif filter_type == "Sepia":
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])
        sepia_frame = cv2.transform(frame, kernel)
        return np.clip(sepia_frame, 0, 255)
    else:
        return frame


def frames_to_video(frames, output_path, fps):
    height, width, layers = frames[0].shape
    size = (width, height)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, size)
    for frame in frames:
        out.write(frame)
    out.release()


def process_video(input_video_path, output_video_path, filter_option):
    start_time = time.time()
    frames = video_to_frames(input_video_path)
    stabilized_frames = stabilize_frames(frames)
    filtered_frames = [apply_filters(frame, filter_option) for frame in stabilized_frames]
    sharpened_frames = [sharpen_frame(frame) for frame in filtered_frames]
    frames_to_video(sharpened_frames, output_video_path, 30)
    end_time = time.time()

    return end_time - start_time, len(frames), output_video_path
