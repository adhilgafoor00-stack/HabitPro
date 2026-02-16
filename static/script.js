function toggleDarkMode(){
    document.body.classList.toggle("light-mode");
    localStorage.setItem("theme",
        document.body.classList.contains("light-mode") ? "light" : "dark");
}

window.onload = function(){
    if(localStorage.getItem("theme")==="light"){
        document.body.classList.add("light-mode");
    }
};
