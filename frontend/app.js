const fileInput = document.getElementById("repoFile");
const dropZone = document.getElementById("dropZone");
const analyzeBtn = document.getElementById("analyzeBtn");
const selectedFile = document.getElementById("selectedFile");
const statusText = document.getElementById("status");
const results = document.getElementById("results");
const findingsContainer = document.getElementById("findings");
const emptyState = document.getElementById("emptyState");
const searchInput = document.getElementById("searchInput");
const severityFilter = document.getElementById("severityFilter");
const progressWrap = document.getElementById("progressWrap");
const progressBar = document.querySelector("#progressBar span");
const progressText = document.getElementById("progressText");
const newAnalysisBtn = document.getElementById("newAnalysisBtn");
let allFindings = [];
let githubUrlInput = null;
let githubReviewBtn = null;
let githubStatus = null;

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function setStatus(message, type = "") {
    statusText.textContent = message;
    statusText.className = "status-message" + (type ? ` ${type}` : "");
}

function formatBytes(bytes) {
    if (!bytes) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / Math.pow(1024, index)).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function shortenPath(path) {
    const value = String(path || "Unknown file").replaceAll("\\", "/");
    const parts = value.split("/");
    return parts.length <= 3 ? value : `.../${parts.slice(-3).join("/")}`;
}

function countSeverity(findings, severity) {
    return findings.filter((finding) => String(finding.severity || "").toUpperCase() === severity).length;
}

function calculateHealth(high, medium, low) {
    return Math.max(0, Math.min(100, Math.round(100 - high * 12 - medium * 6 - low * 2)));
}

function renderAIReview(value) {
    const text = String(value ?? "");
    if (!text.trim()) return "";
    return text.split(/\r?\n/).map((line) => {
        const trimmed = line.trim();
        if (!trimmed) return '<div class="ai-space"></div>';
        if (/^#{1,3}\s+/.test(trimmed)) {
            return `<h4 class="ai-heading">${escapeHtml(trimmed.replace(/^#{1,3}\s+/, ""))}</h4>`;
        }
        const numberMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
        if (numberMatch) return `<div class="ai-list-item"><span class="ai-list-number">${numberMatch[1]}.</span><span>${escapeHtml(numberMatch[2])}</span></div>`;
        const bulletMatch = trimmed.match(/^[-*]\s+(.*)$/);
        if (bulletMatch) return `<div class="ai-list-item"><span class="ai-bullet">•</span><span>${escapeHtml(bulletMatch[1])}</span></div>`;
        const formatted = escapeHtml(trimmed).replace(/`([^`]+)`/g, "<code>$1</code>");
        return `<p>${formatted}</p>`;
    }).join("");
}

function createFindingCard(finding) {
    const severity = ["HIGH", "MEDIUM", "LOW"].includes(String(finding.severity || "LOW").toUpperCase()) ? String(finding.severity).toUpperCase() : "LOW";
    const category = finding.category || "General";
    const rule = finding.rule_id || finding.rule || "STATIC_ANALYSIS";
    const title = finding.title || "Code Finding";
    const description = finding.message || finding.description || "No description available.";
    const recommendation = finding.recommendation || "Review this finding manually.";
    const file = finding.file || "Unknown file";
    const line = finding.line ?? "—";
    const sourceCode = finding.code || finding.source_code || finding.snippet || "";
    const fixedCode = finding.fixed_code || finding.fix || "";
    const aiReview = finding.ai_review || "";
    const card = document.createElement("article");
    card.className = "finding";
    card.innerHTML = `
        <div class="finding-top">
            <span class="severity ${escapeHtml(severity)}">${escapeHtml(severity)}</span>
            <span class="finding-category">${escapeHtml(category)}</span>
            <span class="finding-rule">${escapeHtml(rule)}</span>
        </div>
        <h4>${escapeHtml(title)}</h4>
        <p class="finding-message">${escapeHtml(description)}</p>
        <div class="finding-meta">
            <span>FILE: <b>${escapeHtml(shortenPath(file))}</b></span>
            <span>LINE: <b>${escapeHtml(line)}</b></span>
        </div>
        <div class="finding-meta">
            <span>RECOMMENDATION: <b>${escapeHtml(recommendation)}</b></span>
        </div>
        ${aiReview ? `<div class="ai-review-box"><div class="ai-review-title">ENGINEERING REVIEW · ${escapeHtml(finding.ai_status || "available")}</div><div class="ai-review-content">${renderAIReview(aiReview)}</div></div>` : ""}
        ${sourceCode ? `<div class="code-label">DETECTED CODE</div><pre class="code-block"><code>${escapeHtml(sourceCode)}</code></pre>` : ""}
        ${fixedCode ? `<div class="code-label">SUGGESTED FIX</div><pre class="code-block"><code>${escapeHtml(fixedCode)}</code></pre>` : ""}
    `;
    findingsContainer.appendChild(card);
}

function renderFindings() {
    const query = searchInput.value.trim().toLowerCase();
    const selectedSeverity = severityFilter.value;
    const filtered = allFindings.filter((finding) => {
        const severity = String(finding.severity || "LOW").toUpperCase();
        const text = [finding.title, finding.message, finding.description, finding.recommendation, finding.file, finding.rule, finding.rule_id, finding.category, finding.code, finding.ai_review]
            .map((value) => String(value ?? "")).join(" ").toLowerCase();
        return (selectedSeverity === "ALL" || severity === selectedSeverity) && text.includes(query);
    });
    document.getElementById("findingCount").textContent = `${filtered.length} issue${filtered.length === 1 ? "" : "s"}`;
    findingsContainer.innerHTML = "";
    emptyState.classList.toggle("hidden", filtered.length !== 0);
    filtered.forEach(createFindingCard);
}

function displayResults(data) {
    results.classList.remove("hidden");
    allFindings = Array.isArray(data.findings) ? data.findings : [];
    const high = countSeverity(allFindings, "HIGH");
    const medium = countSeverity(allFindings, "MEDIUM");
    const low = countSeverity(allFindings, "LOW");
    const total = allFindings.length;
    document.getElementById("repoTitle").textContent = data.repository || "Analysis Result";
    document.getElementById("repoMeta").textContent = `${total} finding${total === 1 ? "" : "s"} · Database ID ${data.database_id ?? "—"}`;
    document.getElementById("totalIssues").textContent = total;
    document.getElementById("highIssues").textContent = high;
    document.getElementById("mediumIssues").textContent = medium;
    document.getElementById("lowIssues").textContent = low;
    const score = calculateHealth(high, medium, low);
    document.getElementById("healthScore").textContent = score;
    document.getElementById("healthLabel").textContent = score >= 90 ? "Excellent" : score >= 75 ? "Good" : score >= 55 ? "Needs attention" : "Critical";
    document.getElementById("healthHint").textContent = `${total} issue${total === 1 ? "" : "s"} worth reviewing.`;
    const scoreRing = document.getElementById("scoreRing");
    const degrees = score * 3.6;
    scoreRing.style.background = `radial-gradient(circle, #111827 58%, transparent 60%), conic-gradient(var(--green) ${degrees}deg, rgba(255,255,255,.08) ${degrees}deg)`;
    renderFindings();
}

async function requestJson(url, options) {
    const response = await fetch(url, options);
    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await response.json() : { error: await response.text() };
    if (!response.ok || data.error) throw new Error(data.detail || data.error || "Request failed.");
    return data;
}

async function analyzeRepository() {
    const file = fileInput.files?.[0];
    if (!file) return setStatus("Select a ZIP repository first.", "error");
    if (!file.name.toLowerCase().endsWith(".zip")) return setStatus("Only ZIP repositories are supported.", "error");
    const formData = new FormData();
    formData.append("file", file);
    analyzeBtn.disabled = true;
    analyzeBtn.classList.add("loading");
    progressWrap.style.display = "flex";
    progressBar.style.width = "10%";
    progressText.textContent = "Uploading repository...";
    let progress = 10;
    const timer = setInterval(() => {
        progress = Math.min(progress + Math.random() * 10, 88);
        progressBar.style.width = `${progress}%`;
        progressText.textContent = progress < 40 ? "Scanning repository..." : progress < 70 ? "Checking code rules..." : "Preparing engineering review...";
    }, 450);
    try {
        const data = await requestJson("/review", { method: "POST", body: formData });
        clearInterval(timer);
        progressBar.style.width = "100%";
        progressText.textContent = "Analysis complete ✓";
        displayResults(data);
        setStatus("Analysis completed successfully.", "success");
        results.scrollIntoView({ behavior: "smooth" });
    } catch (error) {
        clearInterval(timer);
        progressWrap.style.display = "none";
        setStatus(`Error: ${error.message}`, "error");
        console.error(error);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.classList.remove("loading");
    }
}

function createGitHubReviewUI() {
    const card = document.createElement("section");
    card.className = "upload-card github-card";
    card.style.marginTop = "20px";
    card.innerHTML = `
        <div class="upload-icon">GH</div>
        <div class="upload-copy">
            <h2>Review a GitHub repository</h2>
            <p>Paste a <strong>public GitHub URL</strong> to clone and analyze it.</p>
            <input id="githubRepoUrl" type="url" placeholder="https://github.com/owner/repository" style="width:min(100%,650px);height:42px;padding:0 12px;border-radius:10px;border:1px solid var(--border);background:#0b101c;color:#fff;outline:0;">
            <div id="githubStatus" class="status-message" style="position:static;margin-top:8px;"></div>
        </div>
        <button id="githubReviewBtn" class="analyze-button" type="button">Review GitHub →</button>
    `;
    dropZone.insertAdjacentElement("afterend", card);
    githubUrlInput = document.getElementById("githubRepoUrl");
    githubReviewBtn = document.getElementById("githubReviewBtn");
    githubStatus = document.getElementById("githubStatus");
    githubReviewBtn.addEventListener("click", reviewGitHubRepository);
    githubUrlInput.addEventListener("keydown", (event) => { if (event.key === "Enter") reviewGitHubRepository(); });
}

async function reviewGitHubRepository() {
    const repoUrl = githubUrlInput.value.trim();
    if (!repoUrl) return setGitHubStatus("Enter a GitHub repository URL.", "error");
    try {
        githubReviewBtn.disabled = true;
        githubStatus.textContent = "Cloning and analyzing repository...";
        const data = await requestJson("/review/github", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repo_url: repoUrl })
        });
        displayResults(data);
        setGitHubStatus("GitHub repository analyzed successfully.", "success");
        results.scrollIntoView({ behavior: "smooth" });
    } catch (error) {
        setGitHubStatus(`Error: ${error.message}`, "error");
    } finally {
        githubReviewBtn.disabled = false;
    }
}

function setGitHubStatus(message, type = "") {
    githubStatus.textContent = message;
    githubStatus.className = "status-message" + (type ? ` ${type}` : "");
}

fileInput.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".zip")) {
        fileInput.value = "";
        selectedFile.textContent = "No repository selected";
        setStatus("Only ZIP repositories are supported.", "error");
        return;
    }
    selectedFile.textContent = `${file.name} · ${formatBytes(file.size)}`;
    setStatus("", "");
});

["dragenter", "dragover"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => { event.preventDefault(); dropZone.classList.add("dragging"); }));
["dragleave", "drop"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => { event.preventDefault(); dropZone.classList.remove("dragging"); }));
dropZone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".zip")) return setStatus("Please drop a ZIP repository.", "error");
    try { fileInput.files = event.dataTransfer.files; } catch (_) {}
    selectedFile.textContent = `${file.name} · ${formatBytes(file.size)}`;
});
analyzeBtn.addEventListener("click", analyzeRepository);
searchInput.addEventListener("input", renderFindings);
severityFilter.addEventListener("change", renderFindings);
newAnalysisBtn.addEventListener("click", () => {
    results.classList.add("hidden");
    fileInput.value = "";
    selectedFile.textContent = "No repository selected";
    progressWrap.style.display = "none";
    progressBar.style.width = "0%";
    progressText.textContent = "Preparing...";
    setStatus("", "");
    allFindings = [];
    findingsContainer.innerHTML = "";
    emptyState.classList.add("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
});

createGitHubReviewUI();

// Lightweight history panel
(async function loadHistory() {
    try {
        const history = await requestJson("/history", { cache: "no-store" });
        if (!Array.isArray(history) || !history.length) return;
        const section = document.createElement("section");
        section.className = "findings-panel";
        section.style.marginTop = "20px";
        section.innerHTML = `<div class="panel-toolbar"><div><h3>Analysis History</h3><span>${history.length} saved review${history.length === 1 ? "" : "s"}</span></div></div><div class="findings-list">${history.slice(0,10).map((item) => `<div class="finding"><h4>${escapeHtml(item.repository)}</h4><div class="finding-meta"><span>ID: <b>${escapeHtml(item.id)}</b></span><span>Findings: <b>${escapeHtml(item.findings_count ?? 0)}</b></span><span>${escapeHtml(item.created_at || "")}</span></div></div>`).join("")}</div>`;
        document.querySelector(".app-shell").appendChild(section);
    } catch (error) {
        console.debug("History unavailable", error);
    }
})();
