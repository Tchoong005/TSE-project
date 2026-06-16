import base64
import binascii
import os
import pickle

import cv2
import face_recognition
import numpy as np

from config import FACE_FOLDER
from database import create_face_profile, get_latest_face_profiles_by_user, get_user_by_id, get_users_by_roles

FACE_MATCH_TOLERANCE = 0.5
FACE_MATCH_MARGIN = 0.08
MIN_STRICT_FACE_RATIO = 0.22
MAX_STRICT_FACE_RATIO = 0.86


def ensure_face_folder():
    if not os.path.exists(FACE_FOLDER):
        os.makedirs(FACE_FOLDER)


def verify_face(user_id):
    ensure_face_folder()
    face_path = os.path.join(FACE_FOLDER, f"{user_id}.pkl")

    if not os.path.exists(face_path):
        return False, "Face profile not registered"

    with open(face_path, "rb") as f:
        registered_encoding = pickle.load(f)

    cap = cv2.VideoCapture(0)
    matched = False

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        cv2.imshow("Press S to Scan Face | Q to Quit", frame)
        key = cv2.waitKey(1)

        if key == ord("s"):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb)

            if len(encodings) == 0:
                cap.release()
                cv2.destroyAllWindows()
                return False, "No face detected"

            current_encoding = encodings[0]
            results = face_recognition.compare_faces(
                [registered_encoding],
                current_encoding,
                tolerance=0.5
            )

            matched = results[0]
            break

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    if matched:
        return True, "Face verified successfully"

    return False, "Face verification failed"


def decode_image_data(image_data):
    if not image_data:
        return None, "No image data received"

    if "," in image_data:
        image_data = image_data.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(image_data)
    except (ValueError, binascii.Error):
        return None, "Invalid image data"

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if frame is None:
        return None, "Unable to read captured image"

    return frame, "Image decoded"


def face_is_complete_and_centered(face_location, landmarks, frame_shape):
    top, right, bottom, left = face_location
    frame_height, frame_width = frame_shape[:2]
    face_width = right - left
    face_height = bottom - top

    if face_width <= 0 or face_height <= 0:
        return False

    width_ratio = face_width / frame_width
    height_ratio = face_height / frame_height

    if width_ratio < MIN_STRICT_FACE_RATIO or height_ratio < MIN_STRICT_FACE_RATIO:
        return False

    if width_ratio > MAX_STRICT_FACE_RATIO or height_ratio > MAX_STRICT_FACE_RATIO:
        return False

    margin_x = frame_width * 0.04
    margin_y = frame_height * 0.04

    if left <= margin_x or right >= frame_width - margin_x:
        return False

    if top <= margin_y or bottom >= frame_height - margin_y:
        return False

    required_features = ["left_eye", "right_eye", "nose_bridge", "top_lip", "bottom_lip"]

    if not all(landmarks.get(feature) for feature in required_features):
        return False

    left_eye = np.mean(landmarks["left_eye"], axis=0)
    right_eye = np.mean(landmarks["right_eye"], axis=0)
    nose = np.mean(landmarks["nose_bridge"], axis=0)
    mouth_points = landmarks["top_lip"] + landmarks["bottom_lip"]
    mouth = np.mean(mouth_points, axis=0)

    eye_distance = abs(right_eye[0] - left_eye[0])

    if eye_distance < frame_width * 0.08:
        return False

    if abs(left_eye[1] - right_eye[1]) > eye_distance * 0.28:
        return False

    if not (left_eye[0] < nose[0] < right_eye[0]):
        return False

    if mouth[1] <= nose[1]:
        return False

    face_center_x = (left + right) / 2
    face_center_y = (top + bottom) / 2
    frame_center_x = frame_width / 2
    frame_center_y = frame_height / 2

    if abs(face_center_x - frame_center_x) > frame_width * 0.20:
        return False

    if abs(face_center_y - frame_center_y) > frame_height * 0.24:
        return False

    return True


def get_face_encoding_from_image_data(image_data, strict=False):
    frame, message = decode_image_data(image_data)

    if frame is None:
        return None, message

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)

    if len(locations) == 0:
        return None, "No face detected"

    if strict and len(locations) > 1:
        return None, "Only one face must be inside the frame"

    landmarks = face_recognition.face_landmarks(rgb, locations)

    if strict and not face_is_complete_and_centered(locations[0], landmarks[0] if landmarks else {}, frame.shape):
        return None, "Face must be fully inside the blue frame and facing the camera"

    encodings = face_recognition.face_encodings(rgb, locations)

    if len(encodings) == 0:
        return None, "Face must face the camera clearly"

    return encodings[0], "Face captured"


def detect_face_from_image_data(image_data):
    encoding, message = get_face_encoding_from_image_data(image_data, strict=True)

    if encoding is None:
        return False, message

    return True, "Face detected"


def match_registered_face_from_image_data(image_data):
    ensure_face_folder()
    current_encoding, message = get_face_encoding_from_image_data(image_data, strict=True)

    if current_encoding is None:
        return None, message

    users = get_users_by_roles(["hr", "employee"])
    best_match = None
    best_distance = None
    second_best_distance = None
    registered_count = 0

    for user in users:
        face_path = os.path.join(FACE_FOLDER, f"{user['id']}.pkl")

        if not os.path.exists(face_path):
            continue

        registered_count += 1

        with open(face_path, "rb") as f:
            registered_encoding = pickle.load(f)

        distance = face_recognition.face_distance(
            [registered_encoding],
            current_encoding
        )[0]

        if best_distance is None or distance < best_distance:
            second_best_distance = best_distance
            best_distance = distance
            best_match = user
        elif second_best_distance is None or distance < second_best_distance:
            second_best_distance = distance

    if registered_count == 0:
        return None, "No registered face profiles found"

    if best_match and best_distance <= FACE_MATCH_TOLERANCE:
        if second_best_distance is not None and second_best_distance - best_distance < FACE_MATCH_MARGIN:
            return None, "Face match is not confident. Move closer and face the camera"

        return best_match, "Face verified successfully"

    return None, "Face not recognised clearly. Move closer and face the camera"


def user_has_face_profile(user_id):
    face_path = os.path.join(FACE_FOLDER, f"{user_id}.pkl")
    return os.path.exists(face_path)


def attach_face_registration_status(users):
    latest_profiles = get_latest_face_profiles_by_user()
    enriched_users = []

    for user in users:
        row = dict(user)
        row["face_registered"] = user_has_face_profile(user["id"]) or user["id"] in latest_profiles
        enriched_users.append(row)

    return enriched_users


def register_face(user_id, registered_by):
    ensure_face_folder()
    user = get_user_by_id(user_id)

    if not user:
        return False, "User not found"

    if user["role"] == "superadmin":
        return False, "Super Admin does not need face registration"

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        cv2.imshow("Press S to capture face", frame)
        key = cv2.waitKey(1)

        if key == ord("s"):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_encodings(rgb)

            if len(faces) == 0:
                cap.release()
                cv2.destroyAllWindows()
                return False, "No face detected"

            encoding = faces[0]
            filename = os.path.join(FACE_FOLDER, f"{user_id}.pkl")

            with open(filename, "wb") as f:
                pickle.dump(encoding, f)

            create_face_profile(user_id, filename, registered_by)

            cap.release()
            cv2.destroyAllWindows()
            return True, "Face registered successfully"

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return False, "Face registration cancelled"


def register_face_from_image_data(user_id, image_data, registered_by):
    ensure_face_folder()
    user = get_user_by_id(user_id)

    if not user:
        return False, "User not found"

    if user["role"] == "superadmin":
        return False, "Super Admin does not need face registration"

    encoding, message = get_face_encoding_from_image_data(image_data, strict=True)

    if encoding is None:
        return False, message

    filename = os.path.join(FACE_FOLDER, f"{user_id}.pkl")

    with open(filename, "wb") as f:
        pickle.dump(encoding, f)

    create_face_profile(user_id, filename, registered_by)
    return True, "Face registered successfully"
