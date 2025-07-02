document.addEventListener("DOMContentLoaded", function() {
  // Mood History Expand/Collapse
  const historyBanner = document.getElementById("moodHistoryBanner");
  const historyContent = document.getElementById("moodHistoryContent");

  if (historyBanner && historyContent) {
    historyBanner.addEventListener("click", function() {
      if (historyContent.style.maxHeight) {
        historyContent.style.maxHeight = null;
        historyBanner.querySelector('h3').innerHTML = '📅 Your Mood History (click to expand)';
      } else {
        historyContent.style.maxHeight = historyContent.scrollHeight + "px";
        historyBanner.querySelector('h3').innerHTML = '📅 Your Mood History (click to collapse)';
      }
    });

    // Initialize as collapsed
    historyContent.style.maxHeight = "0";
    historyContent.style.overflow = "hidden";
    historyContent.style.transition = "max-height 0.3s ease";
  }

  // Mood Summary Toggle
  const toggleBtn = document.getElementById("toggle-summary");
  const summaryContent = document.getElementById("summary-content");
  const toggleIcon = document.getElementById("toggle-icon");

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isOpen = summaryContent.style.display === "block";
      summaryContent.style.display = isOpen ? "none" : "block";
      toggleIcon.textContent = isOpen ? "▼" : "▲";
    });
  }

  // 🧠 Convert predicted tags into a general mood level
  function getMoodLevelFromTags(tags) {
    if (!tags || tags.length === 0) return "Very Happy";

    const moodScore = {
      "depression": 1,
      "suicidal_thoughts": 1,
      "burnout": 2,
      "low self-esteem": 2,
      "anxiety": 2,
      "emotional_instability": 2,
      "stress": 3,
      "neutral": 3,
      "low_energy": 3
    };

    let minScore = 5;
    tags.forEach(tag => {
      const score = moodScore[tag.toLowerCase()];
      if (score && score < minScore) minScore = score;
    });

    const moodMap = {
      1: "Very Sad",
      2: "Sad",
      3: "Neutral",
      4: "Happy",
      5: "Very Happy"
    };

    return moodMap[minScore] || "Neutral";
  }

  // Mood Chart Visualization
  let moodChartInstance = null;

  if (typeof Chart !== 'undefined' && document.getElementById("moodChart")) {
    const moodDataEl = document.getElementById("moodData");
    if (!moodDataEl) {
      console.warn("No mood data found for chart.");
      return;
    }

    const moods = JSON.parse(moodDataEl.textContent);
    const labels = moods.map(m => m.timestamp_day || "");
    const moodValues = moods.map(m => {
      const mood = getMoodLevelFromTags(m.diagnosis_tags || []);
      const states = { "Very Happy": 5, "Happy": 4, "Neutral": 3, "Sad": 2, "Very Sad": 1 };
      return states[mood] || 3;
    });

    if (moodChartInstance) moodChartInstance.destroy();

    const ctx = document.getElementById("moodChart").getContext("2d");

    moodChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Mood Trend",
          data: moodValues,
          borderColor: "#6366f1",
          backgroundColor: "rgba(99, 102, 241, 0.1)",
          fill: true,
          tension: 0.4,
          pointBackgroundColor: "#6366f1",
          pointRadius: 5
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            min: 1,
            max: 5,
            ticks: {
              callback: function(value) {
                const labels = ["", "Very Sad", "Sad", "Neutral", "Happy", "Very Happy"];
                return labels[value];
              }
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                const mood = moods[context.dataIndex];
                return [
                  `Mood: ${getMoodLevelFromTags(mood.diagnosis_tags || [])}`,
                  `Time: ${mood.timestamp_display || mood.timestamp}`,
                  mood.journal_entry ? `Journal: ${mood.journal_entry.substring(0, 30)}...` : ''
                ];
              }
            }
          }
        }
      }
    });
  }

  // Delete button (API version)
  document.querySelectorAll(".delete-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const entryId = btn.getAttribute("data-id");
      if (!confirm("Are you sure you wanna delete this mood entry?")) return;

      try {
        const res = await fetch(`/api/mood/delete/${entryId}`, { method: "POST" });
        const data = await res.json();

        if (res.ok) {
          alert(data.message);
          const moodDiv = document.getElementById(`mood-${entryId}`);
          if (moodDiv) moodDiv.remove();
        } else {
          alert("Error: " + data.error);
        }
      } catch (err) {
        alert("Something went wrong while deleting!");
        console.error(err);
      }
    });
  });

  // Delete button (legacy fallback)
  document.querySelectorAll('.delete-mood-btn').forEach(btn => {
    btn.addEventListener('click', async function () {
      const entry = this.closest('.mood-entry');
      if (confirm('Delete this mood entry?')) {
        try {
          const response = await fetch(`/delete_mood/${entry.dataset.id}`, { method: 'DELETE' });

          if (response.ok) {
            entry.style.opacity = '0';
            setTimeout(() => entry.remove(), 300);
          }
        } catch (error) {
          console.error('Delete failed:', error);
        }
      }
    });
  });

  // Theme toggle
  const settingsToggle = document.getElementById("settingsToggle");
  const settingsDropdown = document.getElementById("settingsDropdown");
  const themeToggleBtn = document.getElementById("toggleTheme");

  if (settingsToggle && settingsDropdown) {
    settingsToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = settingsDropdown.style.display === "block";
      settingsDropdown.style.display = isOpen ? "none" : "block";
    });

    document.addEventListener("click", (e) => {
      if (!settingsDropdown.contains(e.target) && e.target !== settingsToggle) {
        settingsDropdown.style.display = "none";
      }
    }, { passive: true });
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", (e) => {
      e.preventDefault();
      document.body.classList.toggle("dark-mode");
      const theme = document.body.classList.contains("dark-mode") ? "dark" : "light";
      localStorage.setItem("theme", theme);
    });
  }

  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
  }
});
