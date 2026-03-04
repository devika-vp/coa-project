const nodes = document.querySelectorAll(".pipe-node");
const descTitle = document.querySelector(".pipeline-desc-title");
const descText = document.querySelector(".pipeline-desc-text");
const playBtn = document.getElementById("pipeline-play");

const stageData = [
    {
        title: "Instruction Fetch",
        text: "Fetch instruction bits from memory using the Program Counter (PC)."
    },
    {
        title: "Instruction Decode",
        text: "Decode opcode, read registers, and prepare control signals."
    },
    {
        title: "Execute",
        text: "ALU executes: computes addresses, arithmetic, or branch decisions."
    },
    {
        title: "Memory",
        text: "Optional access to data memory for loads and stores."
    },
    {
        title: "Write Back",
        text: "Write the final result back into the register file."
    }
];

function activateStep(index) {
    nodes.forEach(node => node.classList.remove("active"));
    nodes[index].classList.add("active");

    descTitle.textContent = stageData[index].title;
    descText.textContent = stageData[index].text;
}

nodes.forEach(node => {
    node.addEventListener("click", () => {
        activateStep(parseInt(node.dataset.step));
    });
});

let autoPlaying = false;
let currentStep = 0;
let interval;

playBtn.addEventListener("click", () => {
    if (autoPlaying) {
        clearInterval(interval);
        playBtn.textContent = "▶ Auto-play";
        autoPlaying = false;
        return;
    }

    playBtn.textContent = "⏸ Pause";
    autoPlaying = true;

    interval = setInterval(() => {
        activateStep(currentStep);
        currentStep = (currentStep + 1) % 5;
    }, 1200);
});