function initPasswordToggle() {
    document.querySelectorAll("[data-toggle-password]").forEach((button) => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.togglePassword);
            const isPassword = input.type === "password";
            input.type = isPassword ? "text" : "password";
            button.textContent = isPassword ? "Hide" : "Show";
        });
    });
}

function initPasswordRules() {
    const ruleChecks = {
        length: (value) => value.length >= 8,
        letter: (value) => /[A-Za-z]/.test(value),
        number: (value) => /\d/.test(value),
        symbol: (value) => /[^A-Za-z0-9]/.test(value),
    };

    function bindRules(input, rules) {
        if (!input || !rules) {
            return;
        }

        function updateRules() {
            const value = input.value;

            rules.querySelectorAll("[data-rule]").forEach((item) => {
                const passed = ruleChecks[item.dataset.rule](value);
                item.classList.toggle("is-valid", passed);
            });
        }

        input.addEventListener("input", updateRules);
        updateRules();
    }

    bindRules(
        document.getElementById("passwordInput"),
        document.getElementById("passwordRules")
    );

    document.querySelectorAll("[data-password-rules]").forEach((rules) => {
        bindRules(document.getElementById(rules.dataset.passwordRules), rules);
    });
}

function initConfirmPasswordMatch() {
    const password = document.getElementById("newPassword");
    const confirm = document.getElementById("confirmPassword");
    const message = document.getElementById("confirmPasswordMessage");

    if (!password || !confirm || !message) {
        return;
    }

    function updateMatchMessage() {
        const value = password.value;
        const confirmValue = confirm.value;
        const matches = value && confirmValue && value === confirmValue;

        if (!confirmValue) {
            message.textContent = "";
            message.className = "field-error";
            return;
        }

        message.textContent = matches
            ? "Passwords match."
            : "New password and confirm password do not match.";
        message.className = matches ? "field-success" : "field-error";
    }

    password.addEventListener("input", updateMatchMessage);
    confirm.addEventListener("input", updateMatchMessage);
}

function initEmailValidation() {
    const emailInput = document.querySelector("[data-email-check]");
    const message = document.getElementById("emailMessage");

    if (!emailInput || !message) {
        return;
    }

    function updateEmailMessage() {
        if (!emailInput.value) {
            message.textContent = "";
            message.className = "field-error";
            return;
        }

        if (emailInput.validity.valid) {
            message.textContent = "Email format is valid.";
            message.className = "field-success";
            return;
        }

        message.textContent = "Enter a valid email address.";
        message.className = "field-error";
    }

    emailInput.addEventListener("input", updateEmailMessage);
    updateEmailMessage();
}

function initResendCountdown() {
    document.querySelectorAll("[data-resend-button]").forEach((button) => {
        let remaining = Number(button.dataset.resendRemaining || 0);
        const defaultText = button.dataset.resendText || button.textContent;

        function render() {
            if (remaining <= 0) {
                button.disabled = false;
                button.textContent = defaultText;
                return;
            }

            button.disabled = true;
            button.textContent = `Resend OTP in ${remaining}s`;
            remaining -= 1;
            window.setTimeout(render, 1000);
        }

        render();
    });
}

function initDepartmentPositionLink() {
    const roleSelect = document.getElementById("roleSelect");
    const departmentSelect = document.getElementById("departmentSelect");
    const positionSelect = document.getElementById("positionSelect");

    if (!roleSelect || !departmentSelect || !positionSelect || typeof departmentPositions === "undefined") {
        return;
    }

    function fillPositions() {
        const selectedPosition = positionSelect.dataset.selected;
        const positions = departmentPositions[departmentSelect.value] || [];
        positionSelect.innerHTML = "";

        positions.forEach((position) => {
            const option = document.createElement("option");
            option.value = position;
            option.textContent = position;

            if (position === selectedPosition) {
                option.selected = true;
            }

            positionSelect.appendChild(option);
        });

        if (!positions.includes(selectedPosition)) {
            positionSelect.dataset.selected = "";
        }
    }

    function applyRoleDefaults() {
        if (roleSelect.value === "hr") {
            departmentSelect.value = "Human Resource";
        }

        fillPositions();
    }

    roleSelect.addEventListener("change", applyRoleDefaults);
    departmentSelect.addEventListener("change", () => {
        positionSelect.dataset.selected = "";
        fillPositions();
    });

    applyRoleDefaults();
}

function initAccountForm() {
    initPasswordToggle();
    initPasswordRules();
    initDepartmentPositionLink();
    initConfirmPasswordMatch();
    initEmailValidation();
    initResendCountdown();
}
