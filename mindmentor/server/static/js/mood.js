document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("moodForm");
  const resultBox = document.getElementById("predictionResult");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
      age: form.age.value,
      gender: form.gender.value,
      stress_level: form.stress_level.value,
      sleep_hours: form.sleep_hours.value,
      sociability: form.sociability.value,
      anxiety: form.anxiety.value,
      emotional_stability: form.emotional_stability.value,
      self_esteem: form.self_esteem.value,
      motivation: form.motivation.value,
      eating_habits: form.eating_habits.value,
      journal_entry: form.journal_entry.value
    };

    try {
      const res = await fetch("/api/mood/checkin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      const result = await res.json();

      if (res.ok) {
        const tags = result.predicted_tags || [];
        resultBox.innerHTML = `
          <h3>🧠 Mental Health Insights:</h3>
          ${tags.length > 0 ? tags.map(tag => `<span class="tag">${tag}</span>`).join(" ") 
                            : "<p>No diagnosis tags predicted.</p>"}
        `;
        resultBox.style.display = "block";
      } else {
        resultBox.innerHTML = `<p style="color: red;">❌ ${result.error || "Something went wrong"}</p>`;
        resultBox.style.display = "block";
      }
    } catch (err) {
      console.error("🔥 Prediction error:", err);
      resultBox.innerHTML = `<p style="color: red;">🚨 Server error. Try again later.</p>`;
      resultBox.style.display = "block";
    }
  });
});
