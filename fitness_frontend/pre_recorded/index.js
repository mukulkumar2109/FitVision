console.log("hello")
console.log("hello")


const resultDiv = document.getElementById("result");
const resultContent = document.getElementById("resultContent");
let selectedFile = null;
const results = document.getElementById('results');
const messageBox = document.getElementById('messageBox');
console.log(4)
function previewVideo(event) {
    const file = event.target.files[0];
    const videoPreview = document.getElementById('videoPreview');
    const uploadButton = document.getElementById('uploadButton');
    
    if(file && file.type.startsWith('video/')){
        selectedFile = file;
        const fileUrl = URL.createObjectURL(file);
        videoPreview.src = fileUrl;
        videoPreview.style.display = 'block';
        uploadButton.disabled = false;
    } else {
        alert("Please uplaod a valid video file.");
        videoPreview.style.display = 'none';
        uploadButton.disabled = true;
    }
}

async function uploadVideo() {
    if(!selectedFile){
        alert("No video file selected.");
        return;
    }
    
    const formData = new FormData();
    formData.append('video', selectedFile);

    const exerciseInput = document.getElementById('exerciseInput');
    const boddyPartInput = document.getElementById('bodyPartInput');
    const exercise = exerciseInput.value.trim() || 'bicep curls';
    const bodyPart = boddyPartInput.value.trim() || 'left arm';

    formData.append('exercise', exercise);
    formData.append('body_part', bodyPart);

    try{
        messageBox.style.display='block';
        messageBox.textContent = "Processing... Please Wait"
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;

        const response = await fetch('http://127.0.0.1:8000/', {
            method: 'POST',
            headers: {
                ...(csrfToken && { 'X=CSRFToken': csrfToken  })
            }, 
            body: formData,
        });
        if(response.ok) {
            const data = await response.json();
            console.log(data);
            const reps = data.result? data.result.reps : 'Reps not available';
            console.log(data.result.messages)
            console.log(reps);
            const message = data.result.messages? data.result.messages: 'Doing Great';
            messageBox.textContent = `Feedback: ${message}`;
            messageBox.style.display='none'
            // results.textContent = `Reps: ${reps}`;
            
            if (data.result.reps !== undefined && data.result.messages !== undefined) {
                // Display results in the `result` div
                resultDiv.style.display = "block";
                resultContent.textContent = `Repetitions: ${data.result.reps}\nFeedback: ${message}`;
            }

            if(message === "Doing Great"){
                alert('Video uploaded successfully');

            }
            else{
                alert(message)
            }
        } else {
            const errorText = await response.text();
            results.textContent = `Error ${errorText}`;

        }
    }
    catch(error) {
        console.error('Error uploading video:', error);
        messageBox.textContent = `Error: ${error.message}`;
        messageBox.style.display='block'
    }
};

console.log(8)
