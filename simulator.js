// simulator.js

// Animate pipeline stages
function animatePipeline(data) {
    const stages = ["if", "id", "ex", "mem", "wb"];

    stages.forEach(stage => {
        const node = document.getElementById(`step-${stage}`);
        const label = document.getElementById(`label-${stage}`);
        node.classList.remove('active');
        label.innerText = "Waiting...";
    });

    let delay = 0;

    stages.forEach(stage => {
        setTimeout(() => {
            const node = document.getElementById(`step-${stage}`);
            const label = document.getElementById(`label-${stage}`);
            node.classList.add('active');
            label.innerText = data[stage.toUpperCase()];
        }, delay);

        delay += 500;
    });
}

// Main run simulation function
async function runSimulation() {
    const operation = document.getElementById("instrType").value;
    const rs = parseInt(document.getElementById("rsValue").value, 10) || 0;
    const rt = parseInt(document.getElementById("rtValue").value, 10) || 0;

    try {
        const stallFlag = document.getElementById('stallFlag').checked;
        const predBranch = document.getElementById('predBranch').checked ? 1 : 0;

        const response = await fetch("/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ operation, rs, rt, stall: stallFlag, predicted_branch: predBranch })
        });

        if (!response.ok) throw new Error("Server returned an error!");

        const data = await response.json();

        // Add input values to data
        data.operation = operation;
        data.rs = rs;
        data.rt = rt;

        // Store results in sessionStorage
        sessionStorage.setItem('simulationResults', JSON.stringify(data));

        // Redirect to results page
        window.location.href = '/results';

    } catch (error) {
        console.error(error);
        alert("Simulation failed: " + error.message);
    }
}

// Theme toggle
function toggleTheme() {
    document.body.classList.toggle("light");
}

// Event listeners
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("runButton")
        .addEventListener("click", runSimulation);

    document.getElementById("resetButton")
        .addEventListener("click", () => location.reload());
});