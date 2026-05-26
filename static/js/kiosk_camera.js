const video = document.getElementById("camera");
const canvas = document.getElementById("snapshot");
const messageBox = document.getElementById("message");
const modeBadge = document.getElementById("modeBadge");

let scanTimer = null;
let requestInProgress = false;
let pauseUntil = 0;

function setKioskStatus(text, type = "info") {
    messageBox.textContent = text;
    messageBox.className = `kiosk-message ${type}`;
}

async function startKioskCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = stream;
        modeBadge.textContent = "Auto scanning";
        setKioskStatus("Scanning...", "info");
        startAutoScan();
    } catch (error) {
        modeBadge.textContent = "Camera blocked";
        setKioskStatus("Unable to access camera. Please allow camera permission.", "error");
    }
}

function captureKioskFrame() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.9);
}

function startAutoScan() {
    if (scanTimer) {
        clearInterval(scanTimer);
    }

    scanTimer = setInterval(scanFace, 2000);
    scanFace();
}

async function scanFace() {
    if (requestInProgress || Date.now() < pauseUntil) {
        return;
    }

    if (!video.videoWidth || !video.videoHeight) {
        setKioskStatus("Scanning...", "info");
        return;
    }

    requestInProgress = true;
    setKioskStatus("Recognising face...", "info");

    try {
        const image = captureKioskFrame();
        const response = await fetch("/api/kiosk_scan", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ image }),
        });

        const result = await response.json();

        if (result.success) {
            const name = result.employee_name || "Employee";
            setKioskStatus(`Attendance recorded successfully - ${name} (${result.action})`, "success");
            pauseUntil = Date.now() + 5000;
            setTimeout(() => setKioskStatus("Scanning...", "info"), 5000);
            return;
        }

        if (result.message === "No face detected") {
            setKioskStatus("No face detected", "error");
        } else if (result.status === "warning") {
            const name = result.employee_name ? ` - ${result.employee_name}` : "";
            setKioskStatus(`${result.message}${name}`, "warning");
            pauseUntil = Date.now() + 5000;
            setTimeout(() => setKioskStatus("Scanning...", "info"), 5000);
        } else {
            setKioskStatus(result.message || "Face not recognised", "error");
        }
    } catch (error) {
        setKioskStatus("Face not recognised", "error");
    } finally {
        requestInProgress = false;
    }
}

if (video && canvas && messageBox && modeBadge) {
    startKioskCamera();
}
