document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('moodForm');
  const messageBox = document.getElementById('responseMessage');

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
      if (key === 'journal_entry') {
        data[key] = value.trim();
      } else if (key === 'gender') {
        data[key] = value.toLowerCase();
      } else {
        data[key] = parseFloat(value); // convert numeric inputs
      }
    });

    try {
      const res = await fetch('/api/mood/checkin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      const result = await res.json();
      
      console.log('Status:', res.status);
      console.log('Raw result:', result);

      if (res.ok) {
        messageBox.innerHTML = `
          <p>✅ Check-in successful!</p>
          <p>🧠 Predicted tags: <strong>${result.predicted_tags.join(', ')}</strong></p>
        `;
        form.reset();
      } else {
        throw new Error(result.message || 'Unknown error occurred');
      }

    } catch (err) {
      console.error(err);
      messageBox.innerHTML = `<p style="color: red;">❌ ${err.message}</p>`;
    }
  });
});
