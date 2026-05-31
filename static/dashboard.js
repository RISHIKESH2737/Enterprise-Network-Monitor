console.log("Dashboard Loaded")

function toggleSidebar(){
    document.getElementById("sidebar")
        .classList.toggle("collapsed")
}

function toggleTheme(){
    document.body.classList.toggle("light-mode")
}

function openAddDevice(e){
    e.preventDefault()

    document.getElementById("addDeviceModal")
        .style.display="flex"
}

function closeAddDevice(){
    document.getElementById("addDeviceModal")
        .style.display="none"
}