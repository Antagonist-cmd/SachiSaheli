const SUPABASE_URL = "https://dbvjvkdwxlwdidyubtmq.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRidmp2a2R3eGx3ZGlkeXVidG1xIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAwNzc0MzAsImV4cCI6MjA2NTY1MzQzMH0.h3XitBnaMaqgYkuJVcxW3HEiU04yuOD4UlpKCWfe5JM";

const client = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

document.addEventListener("DOMContentLoaded", () => {
  const registerForm = document.getElementById("registerForm");
  const loginForm = document.getElementById("loginForm");

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = registerForm.email.value;
      const password = registerForm.password.value;

      const { data, error } = await client.auth.signUp({ email, password });
      if (error) {
        alert("Registration failed: " + error.message);
      } else {
        alert("✅ Registered! Please check your email.");
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = loginForm.email.value;
      const password = loginForm.password.value;

      const { data, error } = await client.auth.signInWithPassword({ email, password });
      if (error) {
        alert("Login failed: " + error.message);
      } else {
        alert("🎉 Logged in!");
        window.location.href = "/dashboard";
      }
    });
  }
});
