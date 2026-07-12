// CAMERA FUNCTIONALITY (for Verification Page)

// Only run if we are on the verification page
if (document.getElementById('startCameraBtn')) {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');
    const startBtn = document.getElementById('startCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const selfieInput = document.getElementById('selfieInput');
    const selfieUploadFallback = document.getElementById('selfieUploadFallback');
    const submitBtn = document.getElementById('submitBtn');

    let stream = null;
    let capturedBlob = null;

    // --- START CAMERA ---
    if (startBtn) {
        startBtn.addEventListener('click', async function () {
            try {
                stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                    audio: false
                });
                video.srcObject = stream;
                await video.play();

                startBtn.style.display = 'none';
                captureBtn.style.display = 'inline-block';

                showFlashMessage('Camera started! Click "Capture Selfie" to take your photo.', 'success');

            } catch (error) {
                console.error('Camera error:', error);
                alert('Could not access camera. Please ensure you have granted camera permissions, or use the file upload option.');
            }
        });
    }

    // --- CAPTURE PHOTO ---
    if (captureBtn) {
        captureBtn.addEventListener('click', function () {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(function (blob) {
                capturedBlob = blob;

                // Show preview
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewImage.src = e.target.result;
                    previewContainer.style.display = 'block';
                };
                reader.readAsDataURL(blob);

                // Create file from blob and set to hidden input
                const file = new File([blob], 'selfie.jpg', { type: 'image/jpeg' });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                selfieInput.files = dataTransfer.files;
                selfieInput.dispatchEvent(new Event('change'));

                // Update buttons
                captureBtn.style.display = 'none';
                retakeBtn.style.display = 'inline-block';

                showFlashMessage('✅ Selfie captured! Click "Retake" if you want to try again.', 'success');

            }, 'image/jpeg', 0.9);
        });
    }

    // --- RETAKE PHOTO ---
    if (retakeBtn) {
        retakeBtn.addEventListener('click', function () {
            previewContainer.style.display = 'none';
            previewImage.src = '';
            selfieInput.value = '';
            capturedBlob = null;

            retakeBtn.style.display = 'none';
            captureBtn.style.display = 'inline-block';

            showFlashMessage('Selfie cleared. Click "Capture Selfie" to try again.', 'info');
        });
    }

    // --- FALLBACK: Manual file upload ---
    if (selfieUploadFallback) {
        selfieUploadFallback.addEventListener('change', function (e) {
            if (this.files && this.files.length > 0) {
                // Copy the file to the hidden input
                const file = this.files[0];
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                selfieInput.files = dataTransfer.files;
                selfieInput.dispatchEvent(new Event('change'));

                // Show preview
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewImage.src = e.target.result;
                    previewContainer.style.display = 'block';
                };
                reader.readAsDataURL(file);

                showFlashMessage('✅ Selfie photo uploaded!', 'success');
            }
        });
    }

    // --- FORM VALIDATION MOVED TO BACKEND ---

    // --- CLEAN UP CAMERA ON PAGE LEAVE ---
    window.addEventListener('beforeunload', function () {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
}

// HELPER: Flash Message (Bootstrap alert)

function showFlashMessage(message, type = 'info') {
    // Remove existing flash messages
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(el => el.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-2`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    const form = document.getElementById('verificationForm');
    if (form) {
        form.prepend(alertDiv);
    } else {
        document.querySelector('.container').prepend(alertDiv);
    }

    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}