document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("moodForm");
  const resultDiv = document.getElementById("result");
  const suggestionDiv = document.getElementById("suggestions");
  const resultSection = document.getElementById("results");

  if (!form || !resultDiv || !suggestionDiv || !resultSection) {
    console.error("⛔ Required DOM elements not found!");
    return;
  }

  // Initially hide results section
  resultSection.hidden = true;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = new FormData(form);
    const data = {};

    for (let [key, value] of formData.entries()) {
      if (key === "feeling") {
        data[key] = value.trim(); // feeling is text
      } else {
        const num = parseFloat(value);
        data[key] = isNaN(num) ? 0 : num; // fallback if something goes wrong
      }
    }

    try {
      const response = await fetch("http://127.0.0.1:5000/api/predict-mood", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (response.ok && result.mental_state) {
        resultDiv.innerText = `🧠 Mental State: ${result.mental_state}`;
        localStorage.setItem("lastMood", result.mental_state);

        suggestionDiv.innerHTML = "<h3>Suggestions 💡</h3><ul>" +
          result.suggestions.map(s => `<li>${s}</li>`).join("") + "</ul>";

        resultSection.hidden = false;

        // Optional: You can save to Supabase check-in here
        // await saveCheckInToSupabase(data, result.mental_state);

      } else {
        resultDiv.innerText = "⚠️ Prediction failed. Try again.";
        suggestionDiv.innerHTML = "";
        resultSection.hidden = false;
      }
    } catch (error) {
      console.error("🔥 Fetch error:", error);
      resultDiv.innerText = "🚨 Server error. Try again later.";
      suggestionDiv.innerHTML = "";
      resultSection.hidden = false;
    }
  });
});
