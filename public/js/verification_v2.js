document.addEventListener("DOMContentLoaded", function() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startBtn = document.getElementById('startCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const selfieInput = document.getElementById('selfieInput');
    const selfieBase64 = document.getElementById('selfieBase64');
    const selfieUploadFallback = document.getElementById('selfieUploadFallback');
    
    // Only execute if we are on the verification page
    if (!video || !startBtn) return;
    
    let stream = null;

    startBtn.addEventListener('click', async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            video.style.display = 'block';
            await video.play();
            startBtn.style.display = 'none';
            captureBtn.style.display = 'inline-block';
            previewContainer.style.display = 'none';
        } catch (err) {
            alert('Could not access the camera. Please make sure you granted permission. Error: ' + err.message);
        }
    });

    captureBtn.addEventListener('click', () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        const dataUrl = canvas.toDataURL('image/jpeg');
        previewImage.src = dataUrl;
        
        video.style.display = 'none';
        captureBtn.style.display = 'none';
        retakeBtn.style.display = 'inline-block';
        previewContainer.style.display = 'block';
        
        // Store base64 data directly to bypass browser restrictions on file inputs
        selfieBase64.value = dataUrl;
        
        // Convert base64 to File object and set it in the hidden input (Fallback for browsers that support it)
        canvas.toBlob((blob) => {
            try {
                const file = new File([blob], "selfie.jpg", { type: "image/jpeg" });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                selfieInput.files = dataTransfer.files;
            } catch (e) {
                console.log("Browser does not support assigning files to inputs, relying on base64.");
            }
            
            // clear the fallback so we don't submit both
            selfieUploadFallback.value = "";
            selfieInput.removeAttribute('required');
        }, 'image/jpeg');
        
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });

    retakeBtn.addEventListener('click', async () => {
        retakeBtn.style.display = 'none';
        selfieInput.value = "";
        selfieBase64.value = "";
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            video.style.display = 'block';
            await video.play();
            captureBtn.style.display = 'inline-block';
            previewContainer.style.display = 'none';
        } catch (err) {
            alert('Could not access camera: ' + err.message);
            startBtn.style.display = 'inline-block';
        }
    });
    
    selfieUploadFallback.addEventListener('change', (e) => {
        if (selfieUploadFallback.files && selfieUploadFallback.files[0]) {
            selfieInput.value = "";
            
            // Show preview for the uploaded file and set base64 string
            const reader = new FileReader();
            reader.onload = function(e) {
                const dataUrl = e.target.result;
                previewImage.src = dataUrl;
                selfieBase64.value = dataUrl; // Set the base64 value so the backend processes it just like a camera selfie!
                
                previewContainer.style.display = 'block';
                video.style.display = 'none';
                startBtn.style.display = 'none';
                captureBtn.style.display = 'none';
                retakeBtn.style.display = 'inline-block';
            }
            reader.readAsDataURL(selfieUploadFallback.files[0]);
            
            if (stream) stream.getTracks().forEach(track => track.stop());
        }
    });
    
    // Form validation moved entirely to backend to ensure browser compatibility
});
