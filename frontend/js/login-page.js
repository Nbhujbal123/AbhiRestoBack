document.addEventListener("DOMContentLoaded", () => {
  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email).trim());
  }

  const loginForm = document.getElementById("loginForm");
  const loginMobileInput = document.getElementById("loginMobile");
  if (loginMobileInput) {
    loginMobileInput.addEventListener("input", () => {
      loginMobileInput.value = loginMobileInput.value
        .replace(/\D/g, "")
        .slice(0, 10);
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const name = (document.getElementById("loginName")?.value || "").trim();
      const phone = (document.getElementById("loginMobile")?.value || "")
        .replace(/\D/g, "")
        .slice(0, 10);

      if (!name) {
        alert("Please enter your name");
        return;
      }

      if (!/^\d{10}$/.test(phone)) {
        alert("Mobile number must be exactly 10 digits");
        return;
      }

      const submitBtn = loginForm.querySelector('button[type="submit"]');
      const originalText = submitBtn?.textContent || "Sign In";
      if (submitBtn) {
        submitBtn.textContent = "Signing In...";
        submitBtn.disabled = true;
      }

      try {
        const data = await auth.login({ name, phone });

        const user = data.data?.user;
        if (user && user.role === "admin") {
          window.location.href = "admin-dashboard.html";
        } else {
          window.location.href = "home.html";
        }
      } catch (error) {
        alert(error.message || "Login failed. Please try again.");
      } finally {
        if (submitBtn) {
          submitBtn.textContent = originalText;
          submitBtn.disabled = false;
        }
      }
    });
  }

  window.resetLoginOtpStep = function () {
    const step1 = document.getElementById("loginStep1");
    if (step1) step1.style.display = "block";
  };

  window.attachRegisterFormHandler = function () {
    const registerForm = document.getElementById("registerForm");
    if (!registerForm || registerForm.dataset.bound === "1") return;

    registerForm.dataset.bound = "1";

    const mobileInput = document.getElementById("registerMobile");
    if (mobileInput) {
      mobileInput.addEventListener("input", () => {
        mobileInput.value = mobileInput.value.replace(/\D/g, "").slice(0, 10);
      });
    }

    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const name = registerForm
        .querySelector('input[type="text"]')
        .value.trim();
      const email = registerForm
        .querySelector('input[type="email"]')
        .value.trim();
      const mobileInput = document.getElementById("registerMobile");
      const passwordInput = document.getElementById("registerPassword");
      const confirmInput = document.getElementById("registerConfirmPassword");

      const mobile = (mobileInput?.value || "").replace(/\D/g, "");
      if (!/^\d{10}$/.test(mobile)) {
        alert("Mobile number must be exactly 10 digits");
        return;
      }

      if (!isValidEmail(email)) {
        alert("Please enter a valid email address");
        return;
      }

      if (
        !passwordInput ||
        !confirmInput ||
        passwordInput.value !== confirmInput.value
      ) {
        alert("New Password and Confirm Password must be same");
        return;
      }

      const nameParts = name.split(" ");
      const firstName = nameParts.shift() || name;
      const lastName = nameParts.join(" ");

      try {
        await auth.signup({
          first_name: firstName,
          last_name: lastName,
          email,
          phone: mobile,
          password: passwordInput.value,
        });
        window.location.href = "home.html";
      } catch (error) {
        alert(error.message || "Signup failed");
      }
    });
  };

  const registerForm = document.getElementById("registerForm");
  if (registerForm && registerForm.dataset.inlineHandler !== "1") {
    attachRegisterFormHandler();
  }
});
