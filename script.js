async function loadTrainLines() {
    const response = await fetch('./lines.json');
    const lines = await response.json();

    const suspendedcontainer = document.getElementById('suspended');
    const stationnoticecontainer = document.getElementById('stationnotice');
    const noscheduledservicecontainer = document.getElementById('noscheduledservice');
    const okcontainer = document.getElementById('running');

    lines.forEach(line => {
        switch (line.status) {
            case "Suspended":
                suspendedcontainer.style.display = "block"
                var newline = document.createElement("span")
                newline.classList.add("line")
                newline.style.backgroundColor = line.color
                newline.innerHTML = line.name
                suspendedcontainer.appendChild(newline)
                break;
            case "Station notice":
                stationnoticecontainer.style.display = "block"
                var newline = document.createElement("span")
                newline.classList.add("line")
                newline.style.backgroundColor = line.color
                newline.innerHTML = line.name
                stationnoticecontainer.appendChild(newline)
                break;
            case "No scheduled service":
                noscheduledservicecontainer.style.display = "block"
                var newline = document.createElement("span")
                newline.classList.add("line")
                newline.style.backgroundColor = line.color
                newline.innerHTML = line.name
                noscheduledservicecontainer.appendChild(newline)
                break;
            case "Running":
                var newline = document.createElement("span")
                newline.classList.add("line")
                newline.style.backgroundColor = line.color
                newline.innerHTML = line.name
                okcontainer.appendChild(newline)
                break;

            default:
                console.log(line.name + " has an invalid status")
                break;
        }
    });

    var modal = document.getElementById("modal");

    document.querySelectorAll(".line").forEach(lineelement => {
        lineelement.addEventListener("click", () => {
            modal.style.display = "block";
            lines.forEach((line) => {
                var modalcontent = document.getElementById("modal-inner")
                if (line.name == lineelement.innerHTML) {
                    modalcontent.innerHTML = `
                        <h1>${line.name}</h1>
                        <p>${line.notice}</p>
                        <hr>
                    `
                    if (line.stations == undefined || line.stations.length == 0) {
                        modalcontent.innerHTML += `<p>Station list not available</p>`
                    } else {
                        modalcontent.innerHTML += `<h2>Stations</h2>`;
                        var ul = document.createElement("ul")
                        line.stations.forEach(station => {
                            var li = document.createElement("li")
                            li.innerHTML = station
                            ul.appendChild(li)
                        })
                        modalcontent.appendChild(ul)
                    }
                }
            })
        })
    })
    document.getElementById("close").onclick = () => {
        modal.style.display = "none";
    }

    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    window.addEventListener('keydown', (event) => {
        if (event.key === "Escape") {
            modal.style.display = "none";
        }
    })
}

loadTrainLines();
