const profileVideo = document.getElementById("camera");
const profileCanvas = document.getElementById("snapshot");
const profileMessageBox = document.getElementById("message");
const captureButton = document.getElementById("captureButton");
const profileModeBadge = document.getElementById("modeBadge");
const faceStatusPill = document.getElementById("faceStatusPill");

let faceDetected = false;
let detectTimer = null;
let detectRequestInProgress = false;
let registerRequestInProgress = false;

function setProfileStatus(text, type = "info") {
    profileMessageBox.textContent = text;
    profileMessageBox.className = `kiosk-message ${type}`;
}

function setCaptureEnabled(enabled) {
    faceDetected = enabled;
    captureButton.disabled = !enabled || registerRequestInProgress;
}

async function startProfileCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        profileVideo.srcObject = stream;
        profileModeBadge.textContent = "Detecting face";
        setProfileStatus("Camera active. Place the face inside the frame.", "info");
        startFaceDetection();
    } catch (error) {
        profileModeBadge.textContent = "Camera blocked";
        setProfileStatus("Unable to access camera. Please allow camera permission.", "error");
        setCaptureEnabled(false);
    }
}

function captureProfileFrame() {
    profileCanvas.width = profileVideo.videoWidth;
    profileCanvas.height = profileVideo.videoHeight;
    const context = profileCanvas.getContext("2d");
    context.drawImage(profileVideo, 0, 0, profileCanvas.width, profileCanvas.height);
    return profileCanvas.toDataURL("image/jpeg", 0.9);
}

function startFaceDetection() {
    if (detectTimer) {
        clearInterval(detectTimer);
    }

    detectTimer = setInterval(detectFace, 1800);
    detectFace();
}

async function detectFace() {
    if (detectRequestInProgress || registerRequestInProgress) {
        return;
    }

    if (!profileVideo.videoWidth || !profileVideo.videoHeight) {
        profileModeBadge.textContent = "Camera loading";
        setProfileStatus("Camera is still loading.", "info");
        setCaptureEnabled(false);
        return;
    }

    detectRequestInProgress = true;

    try {
        const response = await fetch(captureButton.dataset.detectFaceUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ image: captureProfileFrame() }),
        });
        const result = await response.json();

        if (result.success) {
            profileModeBadge.textContent = "Face detected";
            setProfileStatus("Face detected. You can capture this profile now.", "success");
            setCaptureEnabled(true);
            return;
        }

        profileModeBadge.textContent = "No face detected";
        setProfileStatus(result.message || "No face detected. Move closer and face the camera.", "warning");
        setCaptureEnabled(false);
    } catch (error) {
        profileModeBadge.textContent = "Detection error";
        setProfileStatus("Unable to detect face. Check camera and try again.", "error");
        setCaptureEnabled(false);
    } finally {
        detectRequestInProgress = false;
    }
}

async function registerFace() {
    if (!profileVideo.videoWidth || !profileVideo.videoHeight) {
        setProfileStatus("Camera is still loading.", "warning");
        return;
    }

    if (!faceDetected) {
        setProfileStatus("No face detected. Registration cannot continue until a face is detected.", "warning");
        return;
    }

    registerRequestInProgress = true;
    captureButton.disabled = true;
    setProfileStatus("Registering face...", "info");

    try {
        const response = await fetch(captureButton.dataset.registerFaceUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ image: captureProfileFrame() }),
        });
        const result = await response.json();

        if (result.success) {
            setProfileStatus(result.message, "success");
            profileModeBadge.textContent = "Registered";
            if (faceStatusPill) {
                faceStatusPill.textContent = "Registered";
                faceStatusPill.className = "status-pill status-active";
            }
            captureButton.textContent = "Re-register Face";
            registerRequestInProgress = false;
            setCaptureEnabled(true);
            return;
        }

        setProfileStatus(result.message || "Face registration failed", "error");
        registerRequestInProgress = false;
        setCaptureEnabled(false);
        detectFace();
    } catch (error) {
        setProfileStatus("Face registration failed", "error");
        registerRequestInProgress = false;
        setCaptureEnabled(false);
        detectFace();
    }
}

if (profileVideo && profileCanvas && profileMessageBox && captureButton && profileModeBadge) {
    setCaptureEnabled(false);
    captureButton.addEventListener("click", registerFace);
    startProfileCamera();
}
