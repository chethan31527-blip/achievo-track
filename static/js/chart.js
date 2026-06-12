function drawLineChart(canvas) {
    const labels = JSON.parse(canvas.dataset.labels || "[]");
    const scores = JSON.parse(canvas.dataset.scores || "[]");
    const ctx = canvas.getContext("2d");
    const width = canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    const height = canvas.height = 260 * window.devicePixelRatio;
    const pad = 34 * window.devicePixelRatio;

    ctx.clearRect(0, 0, width, height);
    ctx.lineWidth = 2 * window.devicePixelRatio;
    ctx.strokeStyle = "rgba(255,255,255,.18)";
    ctx.fillStyle = "rgba(255,255,255,.58)";
    ctx.font = `${12 * window.devicePixelRatio}px Arial`;

    for (let i = 0; i <= 4; i++) {
        const y = pad + ((height - pad * 2) / 4) * i;
        ctx.beginPath();
        ctx.moveTo(pad, y);
        ctx.lineTo(width - pad, y);
        ctx.stroke();
    }

    if (!scores.length) return;
    const step = (width - pad * 2) / Math.max(scores.length - 1, 1);

    ctx.beginPath();
    scores.forEach((score, index) => {
        const x = pad + step * index;
        const y = height - pad - (Math.min(score, 100) / 100) * (height - pad * 2);
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "#58d6ff";
    ctx.lineWidth = 4 * window.devicePixelRatio;
    ctx.stroke();

    scores.forEach((score, index) => {
        const x = pad + step * index;
        const y = height - pad - (Math.min(score, 100) / 100) * (height - pad * 2);
        ctx.beginPath();
        ctx.arc(x, y, 4 * window.devicePixelRatio, 0, Math.PI * 2);
        ctx.fillStyle = score === 100 ? "#2ee59d" : "#ffcf5a";
        ctx.fill();
    });

    const shown = labels.length > 10 ? labels.filter((_, i) => i % 5 === 0 || i === labels.length - 1) : labels;
    shown.forEach((label) => {
        const index = labels.indexOf(label);
        const x = pad + step * index;
        ctx.fillStyle = "rgba(255,255,255,.58)";
        ctx.fillText(label, x - 14 * window.devicePixelRatio, height - 8 * window.devicePixelRatio);
    });
}

function renderCharts() {
    document.querySelectorAll("canvas[data-labels]").forEach(drawLineChart);
}

window.addEventListener("load", renderCharts);
window.addEventListener("resize", renderCharts);
