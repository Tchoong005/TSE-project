const profileVideo = document.getElementById("camera");
const profileCanvas = document.getElementById("snapshot");
const profileMessageBox = document.getElementById("message");
const captureButton = document.getElementById("captureButton");
const profileModeBadge = document.getElementById("modeBadge");
const faceStatusPill = document.getElementById("faceStatusPill");

function setProfileStatus(text, type = "info") {
    profileMessageBox.textContent = text;
    profileMessageBox.className = `kiosk-message ${type}`;
}

async function startProfileCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        profileVideo.srcObject = stream;
        profileModeBadge.textContent = "Camera active";
        setProfileStatus("Camera is ready.", "info");
    } catch (error) {
        profileModeBadge.textContent = "Camera blocked";
        setProfileStatus("Unable to access camera. Please allow camera permission.", "error");
    }
}

function captureProfileFrame() {
    profileCanvas.width = profileVideo.videoWidth;
    profileCanvas.height = profileVideo.videoHeight;
    const context = profileCanvas.getContext("2d");
    context.drawImage(profileVideo, 0, 0, profileCanvas.width, profileCanvas.height);
    return profileCanvas.toDataURL("image/jpeg", 0.9);
}

async function registerFace() {
    if (!profileVideo.videoWidth || !profileVideo.videoHeight) {
        setProfileStatus("Camera is still loading.", "warning");
        return;
    }

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
            captureButton.disabled = false;
            return;
        }

        setProfileStatus(result.message || "Face registration failed", "error");
        captureButton.disabled = false;
    } catch (error) {
        setProfileStatus("Face registration failed", "error");
        captureButton.disabled = false;
    }
}

if (profileVideo && profileCanvas && profileMessageBox && captureButton && profileModeBadge) {
    captureButton.addEventListener("click", registerFace);
    startProfileCamera();
}
