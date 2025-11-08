document.addEventListener("DOMContentLoaded", function () {
    const operatorForm = document.getElementById("operatorForm");
    if (operatorForm) {
        operatorForm.addEventListener("submit", handleOperatorSubmit);
    }

    initializeStationSearch();

    const compositionPartContainer = document.getElementById("composition-parts");
    const compositionsContainer = document.getElementById(
        "compositions-container"
    );
    const lineCompositionInput = document.getElementById("lineComposition");

    let draggedItem = null;
    let isFromSource = false;
    let compositionVariants = [];

    window.addCompositionVariant = function (variantName = "") {
        const variantIndex = compositionVariants.length;
        const variantDiv = document.createElement("div");
        variantDiv.className = "composition-variant";
        variantDiv.style.marginBottom = "15px";
        variantDiv.dataset.index = variantIndex;

        variantDiv.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;" class="form-group">
                <input type="text" class="variant-name-input form-make-this-shit-white poppins" 
                       placeholder="Variant name (e.g., Peak Hours, Off-Peak)" 
                       value="${variantName}" 
                       data-variant="${variantIndex}">
                <button type="button" class="smd-component_button-small poppins btn-danger" onclick="removeCompositionVariant(${variantIndex})">
                    <span class="material-symbols-outlined" style="font-size: 20px;">delete</span>
                </button>
            </div>
            <div class="composition-dropzone form-make-this-shit-white" data-variant="${variantIndex}"></div>
        `;

        compositionsContainer.appendChild(variantDiv);
        compositionVariants.push({ name: variantName, parts: [] });

        const dropzone = variantDiv.querySelector(".composition-dropzone");
        const nameInput = variantDiv.querySelector(".variant-name-input");

        nameInput.addEventListener("input", (e) => {
            compositionVariants[variantIndex].name = e.target.value;
            updateCompositionInput();
        });

        setupDropzone(dropzone, variantIndex);
        updateCompositionInput();
    };

    window.removeCompositionVariant = function (index) {
        const variantDiv = document.querySelector(
            `.composition-variant[data-index="${index}"]`
        );
        if (variantDiv) {
            variantDiv.remove();
            compositionVariants[index] = null; 
            updateCompositionInput();
        }
    };

    function setupDraggable(item) {
        item.addEventListener("dragstart", (e) => {
            draggedItem = item;
            const dropzone = item.parentElement;
            isFromSource = !dropzone.classList.contains("composition-dropzone");
            e.dataTransfer.setData("text/plain", item.dataset.part);
            setTimeout(() => {
                item.classList.add("dragging");
            }, 0);
        });

        item.addEventListener("dragend", () => {
            if (draggedItem) {
                draggedItem.classList.remove("dragging");
            }
            draggedItem = null;
        });
    }

    function setupDropzone(dropzone, variantIndex) {
        dropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            const afterElement = getDragAfterElement(dropzone, e.clientX);
            const draggable = document.querySelector(".dragging");
            // Only move elements that are already in this dropzone (reordering)
            if (draggable && draggable.parentElement === dropzone) {
                if (afterElement == null) {
                    dropzone.appendChild(draggable);
                } else {
                    dropzone.insertBefore(draggable, afterElement);
                }
            }
        });

        dropzone.addEventListener("dragenter", (e) => {
            e.preventDefault();
            dropzone.style.border = "2px solid #007bff";
        });

        dropzone.addEventListener("dragleave", () => {
            dropzone.style.border = "2px dashed #ccc";
        });

        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            if (!draggedItem) return;

            if (isFromSource) {
                const newPart = draggedItem.cloneNode(true);
                newPart.classList.remove("dragging");
                const partName = newPart.getAttribute("data-part");
                newPart.style.backgroundImage = `url('/static/assets/icons/${partName}.png')`;
                newPart.addEventListener("click", () => {
                    dropzone.removeChild(newPart);
                    updateCompositionInput();
                });
                setupDraggable(newPart);

                const afterElement = getDragAfterElement(dropzone, e.clientX);
                if (afterElement == null) {
                    dropzone.appendChild(newPart);
                } else {
                    dropzone.insertBefore(newPart, afterElement);
                }
            }

            if (draggedItem) {
                draggedItem.classList.remove("dragging");
            }
            updateCompositionInput();
            dropzone.style.border = "2px dashed #ccc";
        });
    }

    compositionPartContainer
        .querySelectorAll(".composition-part")
        .forEach(setupDraggable);

    function getDragAfterElement(container, x) {
        const draggableElements = [
            ...container.querySelectorAll(".composition-part:not(.dragging)"),
        ];

        return draggableElements.reduce(
            (closest, child) => {
                const box = child.getBoundingClientRect();
                const offset = x - box.left - box.width / 2;
                if (offset < 0 && offset > closest.offset) {
                    return { offset: offset, element: child };
                } else {
                    return closest;
                }
            },
            { offset: Number.NEGATIVE_INFINITY }
        ).element;
    }

    function updateCompositionInput() {
        if (!compositionsContainer || !lineCompositionInput) return;

        const allCompositions = [];
        document
            .querySelectorAll(".composition-variant")
            .forEach((variantDiv, index) => {
                const dropzone = variantDiv.querySelector(
                    ".composition-dropzone"
                );
                const nameInput = variantDiv.querySelector(
                    ".variant-name-input"
                );
                const parts = Array.from(dropzone.children).map((p) =>
                    p.getAttribute("data-part")
                );

                if (parts.length > 0) {
                    allCompositions.push({
                        name: nameInput ? nameInput.value : "",
                        parts: parts.join(","),
                    });
                }
            });

        lineCompositionInput.value = JSON.stringify(allCompositions);
        console.log("Compositions updated:", lineCompositionInput.value);
    }

    window.loadCompositions = function (compositions) {
        if (!compositionsContainer) return;

        // Clear existing variants
        compositionsContainer.innerHTML = "";
        compositionVariants = [];

        // Handle different data formats
        let compositionsArray = [];

        if (Array.isArray(compositions)) {
            compositionsArray = compositions;
        } else if (
            typeof compositions === "string" &&
            compositions.trim() !== ""
        ) {
            // Legacy: single composition string or JSON array
            try {
                const parsed = JSON.parse(compositions);
                compositionsArray = Array.isArray(parsed)
                    ? parsed
                    : [{ name: "", parts: compositions }];
            } catch {
                compositionsArray = [{ name: "", parts: compositions }];
            }
        }

        // Load each composition variant
        if (compositionsArray.length > 0) {
            compositionsArray.forEach((composition, index) => {
                // Handle both old format (string) and new format (object with name and parts)
                let variantName = "";
                let parts = "";

                if (typeof composition === "string") {
                    // Legacy format: just the parts string
                    parts = composition;
                } else if (composition && typeof composition === "object") {
                    // New format: object with name and parts
                    variantName = composition.name || "";
                    parts = composition.parts || "";
                }

                window.addCompositionVariant(variantName);
                const dropzone = document.querySelector(
                    `.composition-dropzone[data-variant="${index}"]`
                );

                if (dropzone && parts) {
                    parts.split(",").forEach((partId) => {
                        if (partId) {
                            const originalPart = document.querySelector(
                                `#composition-parts .composition-part[data-part="${partId}"]`
                            );
                            if (originalPart) {
                                const newPart = originalPart.cloneNode(true);
                                newPart.style.backgroundImage = `url('/static/assets/icons/${partId}.png')`;
                                newPart.addEventListener("click", () => {
                                    dropzone.removeChild(newPart);
                                    updateCompositionInput();
                                });
                                setupDraggable(newPart);
                                dropzone.appendChild(newPart);
                            }
                        }
                    });
                }
            });
        } else {
            // Add one empty variant if none exist
            window.addCompositionVariant();
        }

        updateCompositionInput();
    };
});

async function handleOperatorSubmit(event) {
    event.preventDefault();
    console.log("handleOperatorSubmit called");

    const formData = new FormData(event.target);
    const operatorId = window.operatorUid;

    const data = {
        name: formData.get("name"),
        color: formData.get("color"),
        users: formData
            .get("users")
            .split("\n")
            .filter((s) => s.trim()),
        short: formData.get("short"),
    };

    try {
        const method = operatorId ? "PUT" : "POST";
        const url = operatorId
            ? `/api/operators/${operatorId}`
            : "/api/operators";

        console.log("Sending request:", { method, url, data });

        const response = await fetch(url, {
            method: method,
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const error = await response.json();
            alert(
                "[Server] Error while saving: " +
                    (error.error || "Unknown Error")
            );
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Error while saving: " + error);
    }
}

let currentLine = null;

function showAddLineModal() {
    const modal = document.getElementById("lineModal");
    document.getElementById("lineForm").reset();
    document.getElementById("modalTitle").textContent = "Add New Line";
    document.getElementById("lineId").value = "";
    if (window.noticeEditor) {
        window.noticeEditor.setValue("");
    }
    window.loadCompositions([]); // Load with empty array
    window.loadStations([]); // Clear stations list
    modal.style.display = "block";
    setTimeout(() => {
        modal.classList.add("show");
        if (window.noticeEditor) {
            window.noticeEditor.refresh();
        }
    }, 10);
}

async function editLine(lineName) {
    const line = window.lines.find((l) => l.name === lineName);
    if (!line) {
        console.error("Line not found:", lineName);
        return;
    }

    console.log("Editing Line:", line);
    console.log("Notice:", line.notice);

    document.getElementById("modalTitle").textContent = "Edit line";
    document.getElementById("lineName").value = line.name;
    document.getElementById("lineColor").value = line.color || "#000000";
    document.getElementById("lineStatus").value = line.status || "Running";
    document.getElementById("lineType").value = line.type || "public";

    if (window.noticeEditor) {
        window.noticeEditor.setValue(line.notice || "");
    }

    // Load compositions - supports both old 'composition' and new 'compositions'
    window.loadCompositions(line.compositions || line.composition || []);

    document.getElementById("lineId").value = line.name;

    // Load stations using new interface
    window.loadStations(line.stations || []);

    const modal = document.getElementById("lineModal");
    modal.style.display = "block";
    setTimeout(() => {
        modal.classList.add("show");
        if (window.noticeEditor) {
            window.noticeEditor.refresh();
        }
    }, 20);
}

async function editOperator(operatorName) {
    // ... existing code ...
    const operator = window.operatorName;
    if (!operator) {
        console.error("Operator not found:", operatorName);
        return;
    }

    console.log("Editing Operator:", operator);

    document.getElementById("modalTitle").textContent = "Edit operator";
    document.getElementById("operatorName").value = window.operatorName;

    const response = await fetch("/api/operators");
    const operators = await response.json();
    const operatorData = operators.find((op) => op.uid === window.operatorUid);

    if (operatorData) {
        document.getElementById("operatorColor").value =
            operatorData.color || "#000000";
        document.getElementById("operatorUsers").value = (
            operatorData.users || []
        ).join("\n");
        document.getElementById("operatorShort").value =
            operatorData.short || "";
        document.getElementById("operatorUid").value = operatorData.uid;
    } else {
        console.error("Operator data not found for UID:", window.operatorUid);
    }

    const modal = document.getElementById("operatorModal");
    modal.style.display = "block";
    setTimeout(() => {
        modal.classList.add("show");
    }, 10);
}

async function deleteLine(lineName) {
    // ... existing code ...
    if (!confirm(`Are you sure you want to delete line ${lineName}?`)) return;

    try {
        const response = await fetch("/api/lines/" + lineName, {
            method: "DELETE",
        });

        if (response.ok) {
            window.location.reload();
        } else {
            alert("Error deleting line");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Error deleting line");
    }
}

async function handleLineSubmit(event, uid) {
    event.preventDefault();
    if (window.noticeEditor) {
        const noticeValue = window.noticeEditor.getValue();
        const noticeTextarea = document.querySelector(
            'textarea[name="notice"]'
        );
        if (noticeTextarea) {
            noticeTextarea.value = noticeValue;
        }
    }
    const formData = new FormData(event.target);
    const lineId = document.getElementById("lineId").value;

    // Parse compositions from JSON string
    let compositions = [];
    try {
        const compositionsValue = formData.get("compositions");
        if (compositionsValue) {
            compositions = JSON.parse(compositionsValue);
        }
    } catch (e) {
        console.error("Error parsing compositions:", e);
    }

    const data = {
        name: formData.get("name"),
        color: formData.get("color"),
        status: formData.get("status"),
        type: formData.get("type"),
        notice: formData.get("notice"),
        stations: selectedStations.map((station) => station.name),
        compositions: compositions,
        operator: window.operatorName,
        operator_uid: window.operatorUid,
    };

    try {
        const method = lineId ? "PUT" : "POST";
        const url = lineId ? `/api/lines/${lineId}` : "/api/lines";

        console.log("Sending request:", { method, url, data });

        const response = await fetch(url, {
            // ... existing code ...
            method: method,
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const error = await response.json();
            alert(
                "[Server] Error while saving: " +
                    (error.error || "Unknown Error")
            );
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Error while saving: " + error);
    }
}

function closeLineModal() {
    // ... existing code ...
    const modal = document.getElementById("lineModal");
    modal.classList.remove("show");
    setTimeout(() => {
        modal.style.display = "none";
    }, 300);
}

document.querySelector(".close").addEventListener("click", closeLineModal);

window.addEventListener("click", (event) => {
    const modal = document.getElementById("lineModal");
    if (event.target === modal) {
        closeLineModal();
    }
});

window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeLineModal();
    }
});

function closeOperatorModal() {
    // ... existing code ...
    const modal = document.getElementById("operatorModal");
    modal.classList.remove("show");
    setTimeout(() => {
        modal.style.display = "none";
    }, 300);
}

document
    .querySelector("#closeOperator")
    .addEventListener("click", closeOperatorModal);
window.addEventListener("click", (event) => {
    const modal = document.getElementById("operatorModal");
    if (event.target === modal) {
        closeOperatorModal();
    }
});

window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeOperatorModal();
    }
});

// Station Search and Management System
let selectedStations = [];
let allStations = [];
let searchTimeout;

async function initializeStationSearch() {
    const searchInput = document.getElementById("stationSearch");
    const dropdown = document.getElementById("stationDropdown");
    const stationsList = document.getElementById("stationsList");

    if (!searchInput || !dropdown || !stationsList) {
        return; // Elements not found, probably not on the right page
    }

    // Fetch all stations from API
    try {
        const response = await fetch("/api/stations");
        if (response.ok) {
            allStations = await response.json();
        }
    } catch (error) {
        console.error("Error fetching stations:", error);
    }

    // Setup search input events
    searchInput.addEventListener("input", handleStationSearch);
    searchInput.addEventListener("focus", handleStationSearch);

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove("show");
        }
    });

    // Initialize drag and drop for stations list
    initializeStationDragDrop();

    // Update empty state
    updateStationsDisplay();
}

function handleStationSearch(event) {
    const query = event.target.value.trim().toLowerCase();
    const dropdown = document.getElementById("stationDropdown");

    clearTimeout(searchTimeout);

    if (query.length === 0) {
        dropdown.classList.remove("show");
        return;
    }

    searchTimeout = setTimeout(() => {
        // Filter stations based on search query
        const filteredStations = allStations.filter(
            (station) =>
                station.name.toLowerCase().includes(query) &&
                !selectedStations.find(
                    (selected) => selected.name === station.name
                )
        );

        displayStationDropdown(filteredStations);
    }, 150);
}

function displayStationDropdown(stations) {
    const dropdown = document.getElementById("stationDropdown");

    if (stations.length === 0) {
        dropdown.innerHTML =
            '<div class="station-dropdown-item">No stations found</div>';
    } else {
        dropdown.innerHTML = stations
            .map(
                (station) =>
                    `<div class="station-dropdown-item" onclick="addStation('${station.name}')">
                ${station.name}
            </div>`
            )
            .join("");
    }

    dropdown.classList.add("show");
}

function addStation(stationName) {
    // Don't add duplicates
    if (selectedStations.find((station) => station.name === stationName)) {
        return;
    }

    selectedStations.push({
        name: stationName,
        order: selectedStations.length,
    });

    // Clear search input and hide dropdown
    document.getElementById("stationSearch").value = "";
    document.getElementById("stationDropdown").classList.remove("show");

    updateStationsDisplay();
    updateHiddenInput();
}

function removeStation(index) {
    selectedStations.splice(index, 1);

    // Update order numbers
    selectedStations.forEach((station, i) => {
        station.order = i;
    });

    updateStationsDisplay();
    updateHiddenInput();
}

function updateStationsDisplay() {
    const stationsList = document.getElementById("stationsList");

    if (selectedStations.length === 0) {
        stationsList.className = "stations-list empty";
        stationsList.innerHTML = "";
        return;
    }

    stationsList.className = "stations-list";
    stationsList.innerHTML = selectedStations
        .map(
            (station, index) =>
                `<div class="station-item" draggable="true" data-index="${index}">
            <div class="station-item-order">${index + 1}</div>
            <div class="station-item-name">${station.name}</div>
            <button type="button" class="station-item-remove" onclick="removeStation(${index})">×</button>
        </div>`
        )
        .join("");
}

function updateHiddenInput() {
    const hiddenInput = document.getElementById("lineStations");
    if (hiddenInput) {
        hiddenInput.value = selectedStations
            .map((station) => station.name)
            .join("\n");
    }
}

function initializeStationDragDrop() {
    const stationsList = document.getElementById("stationsList");
    if (!stationsList) return;

    let draggedElement = null;
    let draggedIndex = null;

    // Use event delegation for dynamic elements
    stationsList.addEventListener("dragstart", (e) => {
        if (e.target.classList.contains("station-item")) {
            draggedElement = e.target;
            draggedIndex = parseInt(e.target.dataset.index);
            e.target.classList.add("dragging");
            stationsList.classList.add("drag-over");
        }
    });

    stationsList.addEventListener("dragend", (e) => {
        if (e.target.classList.contains("station-item")) {
            e.target.classList.remove("dragging");
            stationsList.classList.remove("drag-over");
            draggedElement = null;
            draggedIndex = null;

            // Remove any placeholder
            const placeholder = stationsList.querySelector(".drag-placeholder");
            if (placeholder) {
                placeholder.remove();
            }
        }
    });

    stationsList.addEventListener("dragover", (e) => {
        e.preventDefault();

        if (!draggedElement) return;

        const afterElement = getDragAfterElement(stationsList, e.clientY);
        const placeholder = getOrCreatePlaceholder();

        if (afterElement == null) {
            stationsList.appendChild(placeholder);
        } else {
            stationsList.insertBefore(placeholder, afterElement);
        }
    });

    stationsList.addEventListener("drop", (e) => {
        e.preventDefault();

        if (!draggedElement || draggedIndex === null) return;

        const placeholder = stationsList.querySelector(".drag-placeholder");
        if (!placeholder) return;

        // Calculate new index based on placeholder position
        const children = Array.from(stationsList.children);
        const placeholderIndex = children.indexOf(placeholder);
        let newIndex = placeholderIndex;

        // Adjust for placeholder
        if (newIndex > draggedIndex) {
            newIndex--;
        }

        // Move the station in the array
        const movedStation = selectedStations.splice(draggedIndex, 1)[0];
        selectedStations.splice(newIndex, 0, movedStation);

        // Update order numbers
        selectedStations.forEach((station, i) => {
            station.order = i;
        });

        // Update display and hidden input
        updateStationsDisplay();
        updateHiddenInput();

        placeholder.remove();
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [
        ...container.querySelectorAll(".station-item:not(.dragging)"),
    ];

    return draggableElements.reduce(
        (closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;

            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        },
        { offset: Number.NEGATIVE_INFINITY }
    ).element;
}

function getOrCreatePlaceholder() {
    let placeholder = document
        .getElementById("stationsList")
        .querySelector(".drag-placeholder");
    if (!placeholder) {
        placeholder = document.createElement("div");
        placeholder.className = "drag-placeholder";
    }
    return placeholder;
}

// Load stations for editing
window.loadStations = function (stations) {
    selectedStations = [];

    if (Array.isArray(stations)) {
        stations.forEach((stationName, index) => {
            selectedStations.push({
                name: stationName,
                order: index,
            });
        });
    }

    updateStationsDisplay();
    updateHiddenInput();
};
