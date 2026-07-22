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
// ============================================================
// IMAGE PREVIEW (for Job Posting & Verification)
// ============================================================

/**
 * Preview an image when a file is selected
 * Usage: Add onchange="previewImage(event, 'photo', 'imagePreviewContainer', 'imagePreview')"
 */
function previewImage(event, inputId = 'photo', containerId = 'imagePreviewContainer', previewId = 'imagePreview') {
    const file = event.target.files[0];
    const previewContainer = document.getElementById(containerId);
    const previewImage = document.getElementById(previewId);

    if (!previewContainer || !previewImage) {
        console.warn('Preview container or image element not found');
        return;
    }

    if (file) {
        // Check file size (5MB limit)
        if (file.size > 5 * 1024 * 1024) {
            showFlashMessage('File is too large. Maximum size is 5MB.', 'danger');
            event.target.value = '';
            previewContainer.style.display = 'none';
            previewImage.src = '#';
            return;
        }

        // Check file type
        if (!file.type.startsWith('image/')) {
            showFlashMessage('Please select an image file (JPEG, PNG, etc.)', 'danger');
            event.target.value = '';
            previewContainer.style.display = 'none';
            previewImage.src = '#';
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            previewImage.src = e.target.result;
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        previewContainer.style.display = 'none';
        previewImage.src = '#';
    }
}

/**
 * Clear the selected image and hide preview
 */
function clearImage(inputId = 'photo', containerId = 'imagePreviewContainer', previewId = 'imagePreview') {
    const fileInput = document.getElementById(inputId);
    const previewContainer = document.getElementById(containerId);
    const previewImage = document.getElementById(previewId);

    if (fileInput) {
        fileInput.value = '';
    }
    if (previewContainer) {
        previewContainer.style.display = 'none';
    }
    if (previewImage) {
        previewImage.src = '#';
    }
}

/**
 * Auto-initialize image preview for any file input with class 'auto-preview'
 * This automatically adds preview functionality to any input with the class
 */
document.addEventListener('DOMContentLoaded', function () {
    // Find all file inputs with class 'auto-preview'
    const fileInputs = document.querySelectorAll('input[type="file"].auto-preview');

    fileInputs.forEach(function (input) {
        // Generate unique IDs if not present
        const inputId = input.id || 'fileInput_' + Math.random().toString(36).substr(2, 9);
        if (!input.id) {
            input.id = inputId;
        }

        // Create preview container if it doesn't exist
        let previewContainer = document.getElementById(inputId + '_preview_container');
        if (!previewContainer) {
            previewContainer = document.createElement('div');
            previewContainer.id = inputId + '_preview_container';
            previewContainer.className = 'mt-2';
            previewContainer.style.display = 'none';

            const previewImg = document.createElement('img');
            previewImg.id = inputId + '_preview';
            previewImg.className = 'img-fluid rounded';
            previewImg.style.maxHeight = '150px';
            previewImg.style.border = '2px solid #22C55E';
            previewImg.src = '#';

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-sm btn-outline-danger ms-2';
            removeBtn.innerHTML = '<i class="fas fa-times"></i> Remove';
            removeBtn.onclick = function () {
                clearImage(inputId, inputId + '_preview_container', inputId + '_preview');
            };

            previewContainer.appendChild(previewImg);
            previewContainer.appendChild(removeBtn);
            input.parentNode.insertBefore(previewContainer, input.nextSibling);
        }

        // Add event listener for file selection
        input.removeEventListener('change', function () { });
        input.addEventListener('change', function (e) {
            previewImage(e, inputId, inputId + '_preview_container', inputId + '_preview');
        });
    });
});