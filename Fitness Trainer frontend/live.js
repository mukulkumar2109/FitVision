let mediaRecorder;
const videoElement = document.getElementById('videoElement');
const recordedChunks = [];

async function startRecording() {
    const exercise = document.getElementById('exerciseInput').value || 'bicep curls';
    const bodyPart = document.getElementById('bodyPartInput').value || 'left arm';

    const data = {
        exercise: exercise,
        body_part: bodyPart
    };

    try {
        // Access the camera
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoElement.srcObject = stream; // Show the camera feed on the video element

        // Create a MediaRecorder instance
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.start(); // Start recording

        // Send data to backend
        const response = await fetch('http://127.0.0.1:8000/live_exercise', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const responseMessage = document.getElementById('responseMessage');

        if (response.ok) {
            const result = await response.json();
            responseMessage.textContent = `Recording started: ${JSON.stringify(result)}`;
        } else {
            const errorText = await response.text();
            responseMessage.textContent = `Error starting recording: ${errorText}`;
        }
    } catch (error) {
        console.error('Error starting recording:', error);
        document.getElementById('responseMessage').textContent = `Error: ${error.message}`;
    }
}

async function stopRecording() {
    try {
        mediaRecorder.stop(); // Stop recording
        mediaRecorder.onstop = async () => {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            const videoURL = URL.createObjectURL(blob);

            // Display the recorded video
            const responseMessage = document.getElementById('responseMessage');
            responseMessage.innerHTML += `<br><video src="${videoURL}" controls></video>`;
        };

        // Stop the video stream
        videoElement.srcObject.getTracks().forEach(track => track.stop());

        // Send request to stop the video feed
        const response = await fetch('http://127.0.0.1:8000/stop_video_feed', {
            method: 'POST'
        });

        const responseMessage = document.getElementById('responseMessage');

        if (response.ok) {
            const result = await response.json();
            responseMessage.textContent = `Recording stopped: ${JSON.stringify(result)}`;
        } else {
            const errorText = await response.text();
            responseMessage.textContent = `Error stopping recording: ${errorText}`;
        }
    } catch (error) {
        console.error('Error stopping recording:', error);
        document.getElementById('responseMessage').textContent = `Error: ${error.message}`;
    }
}