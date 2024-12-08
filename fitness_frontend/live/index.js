let ws; // WebSocket variable
const videoElement = document.getElementById("video");
const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const resultDiv = document.getElementById("result");
const resultContent = document.getElementById("resultContent");

// Add event listener for starting the stream
startButton.addEventListener("click", () => {
    const exercise = document.getElementById("exercise").value;
    const bodyPart = document.getElementById("bodyPart").value;

    if (!exercise || !bodyPart) {
        alert("Please select both exercise and body part.");
        return;
    }
    videoElement.style.display="block";
    // Initialize WebSocket connection
    ws = new WebSocket("ws://127.0.0.1:8000/ws/video-stream/");

    ws.onopen = () => {
        console.log("WebSocket connection established.");
        ws.send(JSON.stringify({ command: "start", exercise, bodyPart }));

        // Update UI states
        startButton.style.display = "none";
        stopButton.style.display = "block";
        resultDiv.style.display = "none";
        resultContent.textContent = ""; // Clear previous results
    };

    ws.onmessage = (event) => {
        if (event.data instanceof Blob) {
            // Handle binary frame data
            const blob = new Blob([event.data], { type: "image/jpeg" });
            const url = URL.createObjectURL(blob);
            videoElement.src = url;
            videoElement.onload = () => {
                URL.revokeObjectURL(url);
            };
            console.log("Received video frame (Blob).");
        } else {
            // Handle JSON results
            try {
                const data = JSON.parse(event.data);
                console.log("Parsed JSON data:", data);
                if (data.reps !== undefined && data.time_taken !== undefined) {
                    // Display results in the `result` div
                    resultDiv.style.display = "block";
                    resultContent.textContent = `Repetitions: ${data.reps}\nTime Taken: ${data.time_taken} seconds`;
                }
            } catch (e) {
                console.error("Error parsing JSON:", e);
            }
        }
    };

    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        alert("WebSocket encountered an error. Please try again.");
        resetUIState();
    };

    ws.onclose = () => {
        console.log("WebSocket connection closed.");
        resetUIState();
    };
});

// Add event listener for stopping the stream
stopButton.addEventListener("click", () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command: "stop" }));
    } else {
        alert("WebSocket is not open or already closed.");
    }
    resetUIState()
});

// Reset UI state when WebSocket is closed or errored
function resetUIState() {
    startButton.style.display = "block";
    stopButton.style.display = "none";
}
