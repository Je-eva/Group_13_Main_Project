function uploadVideo() {
    const input = document.getElementById("videoUpload");
    const file = input.files[0];

    if (!file) {
        alert("Please select a video file.");
        return;
    }

    let formData = new FormData();
    formData.append("video", file);

    const resultMessage = document.getElementById("resultMessage");
    const anomalyFrameContainer = document.getElementById("anomalyFrameContainer");
    const anomalyFrame = document.getElementById("anomalyFrame");

    anomalyFrameContainer.style.display = "none";  // Hide frame before new upload
    resultMessage.innerText = "Processing...";

    fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        resultMessage.innerText = data.message;

        if (data.frame_url) {
            let timestamp = new Date().getTime();  // Prevent browser caching
            anomalyFrame.src = `http://127.0.0.1:5000/detected_frame?time=${timestamp}`;
            anomalyFrameContainer.style.display = "block";
        } else {
            resultMessage.innerText = "No anomaly detected.";
            anomalyFrameContainer.style.display = "none";
        }
    })
    .catch(error => {
        console.error("Error uploading video:", error);
        resultMessage.innerText = "Error processing video.";
    });
}

f// Function to start live feed
function startLiveFeed() {
    const liveFeed = document.getElementById("liveFeedFrame");
    liveFeed.style.display = "block"; // Show the image
    liveFeed.src = "http://127.0.0.1:5000/live_feed"; // Streaming endpoint

    // Start live feed in the backend
    fetch("http://127.0.0.1:5000/start_live_feed")
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        document.getElementById("liveFeedMessage").innerText = data.message;
    })
    .catch(error => {
        console.error("Error starting live feed:", error);
        document.getElementById("liveFeedMessage").innerText = "Error starting live feed.";
    });
}

// Function to stop live feed
function stopLiveFeed() {
    fetch("http://127.0.0.1:5000/stop_live_feed")
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        document.getElementById("liveFeedMessage").innerText = data.message;

        // Stop the image from continuously loading new frames
        const liveFeed = document.getElementById("liveFeedFrame");
        liveFeed.src = "";  // Clear the image source to stop fetching
        liveFeed.style.display = "none"; // Hide feed
    })
    .catch(error => {
        console.error("Error stopping live feed:", error);
        document.getElementById("liveFeedMessage").innerText = "Error stopping live feed.";
    });
}



// Function to open tabs
function openTab(evt, tabName) {
    let tabcontent = document.getElementsByClassName("tabcontent");
    for (let i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    let tablinks = document.getElementsByClassName("tablinks");
    for (let i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("active");
    }

    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.classList.add("active");
}

// Set default tab on page load
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("defaultTab").click();
});
