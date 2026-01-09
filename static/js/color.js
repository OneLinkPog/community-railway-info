function setContrastColor(elementId, color) {
    const element = document.getElementById(elementId);
    if (!element) return;

    try {
        const hex = color.replace("#", "");
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        const brightness = (r * 299 + g * 587 + b * 114) / 1000;

        element.style.color = brightness > 128 ? "#000000" : "#ffffff";
    } catch (error) {
        console.error(`Error setting colors for ${elementId}:`, error);
    }
}

function getContrastColor(color) {
    try {
        const hex = color.replace("#", "");
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        const brightness = (r * 299 + g * 587 + b * 114) / 1000;

        return brightness > 128 ? "#000000" : "#ffffff";
    } catch (error) {
        console.error("Error calculating contrast color:", error);
        return "#000000";
    }
}
