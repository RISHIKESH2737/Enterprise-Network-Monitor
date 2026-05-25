// =========================
// SEARCH FILTER
// =========================

const searchInput =
    document.getElementById("searchInput");

searchInput.addEventListener(
    "keyup",
    function () {

        const value =
            searchInput.value.toLowerCase();

        const cards =
            document.querySelectorAll(
                ".device-card"
            );

        cards.forEach(card => {

            const text =
                card.innerText.toLowerCase();

            if (text.includes(value)) {

                card.style.display = "block";

            } else {

                card.style.display = "none";

            }

        });

    }
);

// =========================
// INITIAL DATA
// =========================

const deviceNames =
    initialData.results.map(
        d => d.name
    );

const responseTimes =
    initialData.results.map(
        d => d.response_time
    );

// =========================
// RESPONSE CHART
// =========================

const responseCtx =
    document.getElementById(
        "responseChart"
    );

const responseChart =
    new Chart(responseCtx, {

        type: "line",

        data: {

            labels: deviceNames,

            datasets: [{

                label: "Response Time (ms)",

                data: responseTimes,

                tension: 0.4,

                fill: true,

                borderWidth: 3,

                pointRadius: 5,

                backgroundColor:
                    "rgba(37,99,235,0.15)",

                borderColor:
                    "#3b82f6"

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    labels: {

                        color: "white"

                    }

                }

            },

            scales: {

                x: {

                    ticks: {

                        color: "white"

                    },

                    grid: {

                        color:
                            "rgba(255,255,255,0.05)"

                    }

                },

                y: {

                    ticks: {

                        color: "white"

                    },

                    grid: {

                        color:
                            "rgba(255,255,255,0.05)"

                    }

                }

            }

        }

    });

// =========================
// STATUS PIE CHART
// =========================

const statusCtx =
    document.getElementById(
        "statusChart"
    );

const statusChart =
    new Chart(statusCtx, {

        type: "doughnut",

        data: {

            labels: [

                "Online",
                "Offline"

            ],

            datasets: [{

                data: [

                    initialData.online_devices,
                    initialData.offline_devices

                ],

                backgroundColor: [

                    "#22c55e",
                    "#ef4444"

                ],

                borderWidth: 0

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    labels: {

                        color: "white"

                    }

                }

            }

        }

    });

// =========================
// SOCKET.IO
// =========================

const socket = io();

// =========================
// LIVE UPDATE
// =========================

socket.on(
    "network_update",
    function(data) {

        console.log(
            "Live Update:",
            data
        );

        // =========================
        // UPDATE STATS
        // =========================

        document.getElementById(
            "totalDevices"
        ).innerText =
            data.total_devices;

        document.getElementById(
            "onlineDevices"
        ).innerText =
            data.online_devices;

        document.getElementById(
            "offlineDevices"
        ).innerText =
            data.offline_devices;

        document.getElementById(
            "avgResponse"
        ).innerText =
            data.avg_response + " ms";

        // =========================
        // UPDATE CARDS
        // =========================

        const container =
            document.getElementById(
                "deviceContainer"
            );

        container.innerHTML = "";

        data.results.forEach(device => {

            const statusClass =

                device.status === "ONLINE"

                ?

                "online-status"

                :

                "offline-status";

            const responseText =

                device.status === "ONLINE"

                ?

                `${device.response_time} ms`

                :

                "Timeout";

            const card = `

                <div class="device-card">

                    <div class="device-top">

                        <i class="fa-solid fa-desktop"></i>

                    </div>

                    <h3>${device.name}</h3>

                    <p class="ip-text">
                        ${device.ip}
                    </p>

                    <span class="status ${statusClass}">
                        ${device.status}
                    </span>

                    <p class="response">
                        Response:
                        ${responseText}
                    </p>

                    <p class="timestamp">
                        Last Scan:
                        ${device.timestamp}
                    </p>

                </div>

            `;

            container.innerHTML += card;

        });

        // =========================
        // UPDATE LINE CHART
        // =========================

        responseChart.data.labels =

            data.results.map(
                d => d.name
            );

        responseChart.data.datasets[0].data =

            data.results.map(
                d => d.response_time
            );

        responseChart.update();

        // =========================
        // UPDATE PIE CHART
        // =========================

        statusChart.data.datasets[0].data = [

            data.online_devices,
            data.offline_devices

        ];

        statusChart.update();

    }
);