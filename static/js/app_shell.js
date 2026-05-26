function initSidebarShell() {
    const sidebar = document.getElementById("appSidebar");
    const layout = document.querySelector(".layout");
    const toggle = document.querySelector("[data-sidebar-toggle]");

    if (!sidebar || !layout || !toggle) {
        return;
    }

    const savedState = localStorage.getItem("eas_sidebar_collapsed");
    const isCollapsed = savedState === "true";
    layout.classList.toggle("sidebar-collapsed", isCollapsed);

    toggle.addEventListener("click", () => {
        const collapsed = !layout.classList.contains("sidebar-collapsed");
        layout.classList.toggle("sidebar-collapsed", collapsed);
        localStorage.setItem("eas_sidebar_collapsed", String(collapsed));
    });
}

document.addEventListener("DOMContentLoaded", initSidebarShell);

window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
        window.location.reload();
    }
});
