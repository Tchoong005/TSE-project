function initDashboardTabs() {
    document.querySelectorAll("[data-tabs]").forEach((tabs) => {
        const buttons = tabs.querySelectorAll("[data-tab-target]");

        buttons.forEach((button) => {
            button.addEventListener("click", () => {
                buttons.forEach((item) => item.classList.remove("is-active"));
                document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("is-active"));
                button.classList.add("is-active");
                document.getElementById(button.dataset.tabTarget).classList.add("is-active");
            });
        });
    });
}

document.addEventListener("DOMContentLoaded", initDashboardTabs);
