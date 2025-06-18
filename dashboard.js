// client/js/dashboard.js

document.addEventListener("DOMContentLoaded", () => {
    const result = localStorage.getItem("lastMood");
    const moodDisplay = document.getElementById("moodResult");
  
    if (result) {
      moodDisplay.innerText = result;
    } else {
      moodDisplay.innerText = "No mood data yet.";
    }
  
    // Mock chart data (you can enhance it later)
    const ctx = document.getElementById("moodChart").getContext("2d");
    const chart = new Chart(ctx, {
      type: "pie",
      data: {
        labels: ["Happy", "Stressed", "Sad", "Neutral"],
        datasets: [{
          label: "Mood History",
          data: [2, 3, 1, 4], // Fake data
          backgroundColor: ["#28a745", "#dc3545", "#ffc107", "#17a2b8"]
        }]
      }
    });
  });
  