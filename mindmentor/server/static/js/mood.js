document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("moodForm");
  const resultDiv = document.getElementById("result");
  const suggestionDiv = document.getElementById("suggestions");
  const resultsSection = document.getElementById("results");
  const saveBtn = document.getElementById("saveBtn");

  if (!form || !resultDiv || !suggestionDiv || !resultsSection || !saveBtn) {
    console.error("⛔ Required DOM elements not found!");
    return;
  }

  let latestPrediction = null;  // Store the last prediction data for saving

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    // Collect form input values
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
      // Convert numeric fields to numbers, keep others as strings
      data[key] = key === "journal_entry" ? value : parseFloat(value);
    }
    
    data["journal_entry"] = form.querySelector("#journal_entry").value || "";
    // Add journal entry if present
    const journalEntry = form.querySelector("#journal_entry").value.trim();
    if (journalEntry) {
      data.journal_entry = journalEntry;
    }

    try {
      // Predict mood
      const response = await fetch("/api/mood/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (result.mental_state) {
        // Display mood & suggestions
        resultDiv.innerText = `🧠 Mental State: ${result.mental_state}`;
        suggestionDiv.innerHTML =
          "<h3>Suggestions 💡</h3><ul>" +
          result.suggestions.map((s) => `<li>${s}</li>`).join("") +
          "</ul>";

        // Show results section
        resultsSection.hidden = false;

        // Save prediction data for later save button click
        latestPrediction = {
          ...data,
          mental_state: result.mental_state,
          suggestions: result.suggestions,
          // Journal entry is already included in data from formData
        };
      } else {
        resultDiv.innerText = "⚠️ Failed to predict mental state.";
        suggestionDiv.innerHTML = "";
        resultsSection.hidden = true;
        latestPrediction = null;
      }
    } catch (error) {
      console.error("🔥 Error during prediction:", error);
      resultDiv.innerText = "🚨 Something went wrong!";
      suggestionDiv.innerHTML = "";
      resultsSection.hidden = true;
      latestPrediction = null;
    }
  });

  saveBtn.addEventListener("click", async function () {
    if (!latestPrediction) {
      alert("Please fill out the form and analyze your mood before saving!");
      return;
    }

    try {
      const saveResponse = await fetch("/api/mood/checkin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(latestPrediction),
      });

      if (saveResponse.ok) {
        alert("✅ Mood check-in saved successfully!");
        // Optionally reset form and hide results
        form.reset();
        resultsSection.hidden = true;
        latestPrediction = null;
        resultDiv.innerText = "";
        suggestionDiv.innerHTML = "";
      } else {
        alert("⚠️ Failed to save mood check-in. Please try again.");
      }
    } catch (error) {
      console.error("🔥 Error during saving check-in:", error);
      alert("🚨 Something went wrong while saving your mood check-in.");
    }
  });
});
