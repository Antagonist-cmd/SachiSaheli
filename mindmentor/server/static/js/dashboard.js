document.addEventListener("DOMContentLoaded", function() {
  // Mood History Expand/Collapse
  const historyBanner = document.getElementById("moodHistoryBanner");
  const historyContent = document.getElementById("moodHistoryContent");
  const bannerTitle = historyBanner ? historyBanner.querySelector('h3') : null;
  
  if (historyBanner && historyContent) {
    historyContent.style.overflow = "hidden";
    historyContent.style.transition = "max-height 0.3s cubic-bezier(0.4,0,0.2,1)";
    historyContent.style.maxHeight = "0px";
    let isOpen = false;
    
    historyBanner.addEventListener("click", function() {
      if (isOpen) {
        historyContent.style.maxHeight = "0px";
        if (bannerTitle) bannerTitle.innerHTML = '📅 Your Mood History (click to expand)';
        isOpen = false;
      } else {
        historyContent.style.maxHeight = historyContent.scrollHeight + "px";
        if (bannerTitle) bannerTitle.innerHTML = '📅 Your Mood History (click to collapse)';
        isOpen = true;
      }
    });
    
    window.addEventListener("resize", function() {
      if (isOpen) {
        historyContent.style.maxHeight = historyContent.scrollHeight + "px";
      }
    });
  }

  // Mood Summary Toggle
  const toggleBtn = document.getElementById("toggle-summary");
  const summaryContent = document.getElementById("summary-content");
  const toggleIcon = document.getElementById("toggle-icon");
  
  if (toggleBtn && summaryContent && toggleIcon) {
    summaryContent.style.display = "none";
    toggleIcon.textContent = "▼";
    
    toggleBtn.addEventListener("click", () => {
      const isOpen = summaryContent.style.display === "block";
      summaryContent.style.display = isOpen ? "none" : "block";
      toggleIcon.textContent = isOpen ? "▼" : "▲";
    });
  }

  // Delete button handlers
  initializeDeleteButtons();

  // Theme toggle
  initializeThemeToggle();
});

// 🧠 Convert predicted tags into a general mood level
function getMoodLevelFromTags(mood_entry) {
  const validMoods = ["Very Sad", "Sad", "Neutral", "Happy", "Very Happy"];
  if (mood_entry && validMoods.includes(mood_entry.simple_mood)) {
    return mood_entry.simple_mood;
  }
  
  const tags = mood_entry?.diagnosis_tags || [];
  if (!Array.isArray(tags) || tags.length === 0) return "Neutral";
  
  const moodScore = {
    // Score 1: Very Sad
    "suicidal thoughts": 1,
    "depression": 1,
    "hopelessness": 1,
    "severe depression": 1,
    "major depression": 1,
    // Score 2: Sad
    "anxiety": 2,
    "burnout": 2,
    "insomnia": 2,
    "stress": 2,
    "low motivation": 2,
    "low self-esteem": 2,
    "emotional instability": 2,
    "isolation": 2,
    "social withdrawal": 2,
    "substance abuse": 2,
    "disordered eating": 2,
    "mood swings": 2,
    "apathy": 2,
    "addiction": 2,
    "substance dependence": 2,
    // Score 3: Neutral
    "neutral": 3,
    "okay": 3,
    "unknown": 3,
    // Score 4: Happy
    "healthy": 4,
    "motivated": 4,
    "balanced": 4,
    "stable": 4,
    "calm": 4,
    "focused": 4,
    "good mood": 4,
    "positive": 4,
    "content": 4,
    "relaxed": 4,
    // Score 5: Very Happy
    "very happy": 5,
    "gratitude": 5,
    "joy": 5,
    "excited": 5,
    "elated": 5,
    "euphoric": 5,
    "blissful": 5,
    "thriving": 5,
    "excellent": 5
  };
  
  let score = 3;
  let found = false;
  
  for (let tag of tags) {
    const normalized = tag.toLowerCase().trim().replace(/[_\s]+/g, " ");
    const s = moodScore[normalized];
    if (s !== undefined) {
      score = Math.min(score, s);
      found = true;
    }
  }
  
  if (!found) {
    console.warn("No valid tags found in", tags);
    return "Neutral";
  }
  
  const moodMap = {
    1: "Very Sad", 2: "Sad", 3: "Neutral", 4: "Happy", 5: "Very Happy"
  };
  return moodMap[score];
}

// Delete button handlers
function initializeDeleteButtons() {
  // API version delete buttons
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
  
  // Legacy fallback delete buttons
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
}

// Theme toggle initialization
function initializeThemeToggle() {
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
  
  // Apply saved theme
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
  }
}