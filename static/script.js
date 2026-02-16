// -------------------- SUCCESS MESSAGE --------------------
function showMessage(text) {
    let msg = document.createElement("div");
    msg.innerText = text;
    msg.className = "popup-message";

    document.body.appendChild(msg);

    setTimeout(() => {
        msg.remove();
    }, 2000);
}

// -------------------- MARK DONE BUTTON --------------------
document.addEventListener("DOMContentLoaded", function () {

    let doneButtons = document.querySelectorAll(".done-btn");

    doneButtons.forEach(btn => {
        btn.addEventListener("click", function () {
            btn.innerText = "✔ Completed";
            btn.style.background = "limegreen";
            btn.style.pointerEvents = "none";
        });
    });

});

// -------------------- DARK MODE TOGGLE --------------------
function toggleDarkMode() {
    document.body.classList.toggle("light-mode");

    if (document.body.classList.contains("light-mode")) {
        localStorage.setItem("theme", "light");
    } else {
        localStorage.setItem("theme", "dark");
    }
}

// -------------------- LOAD SAVED THEME --------------------
window.onload = function () {
    let savedTheme = localStorage.getItem("theme");

    if (savedTheme === "light") {
        document.body.classList.add("light-mode");
    }
};
