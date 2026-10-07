/**
 * AeroAssist AI - Frontend JavaScript & Multi-Agent Orchestration UI
 */

document.addEventListener("DOMContentLoaded", () => {
  // Check if we are on the AI Resolution page
  const runBtn = document.getElementById("btn-run-multi-agent");
  if (runBtn) {
    runBtn.addEventListener("click", handleRunMultiAgent);
  }

  // Quick fill ticket helper
  const quickFillBtns = document.querySelectorAll(".quick-fill-btn");
  quickFillBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const title = btn.getAttribute("data-title");
      const desc = btn.getAttribute("data-desc");
      const cat = btn.getAttribute("data-cat");
      const flight = btn.getAttribute("data-flight");
      const pnr = btn.getAttribute("data-pnr");

      if (document.getElementById("title")) document.getElementById("title").value = title || "";
      if (document.getElementById("description")) document.getElementById("description").value = desc || "";
      if (document.getElementById("category")) document.getElementById("category").value = cat || "Auto-Classify";
      if (document.getElementById("flight_number")) document.getElementById("flight_number").value = flight || "";
      if (document.getElementById("booking_ref")) document.getElementById("booking_ref").value = pnr || "";
    });
  });
});

/**
 * Executes the sequential 5-agent workflow via AJAX and animates each step.
 */
async function handleRunMultiAgent() {
  const btn = document.getElementById("btn-run-multi-agent");
  const ticketId = btn.getAttribute("data-ticket-id");
  const liveContainer = document.getElementById("agent-live-execution");
  const resultsContainer = document.getElementById("multi-agent-results-view");
  const spinner = document.getElementById("agent-spinner");

  btn.disabled = true;
  if (spinner) spinner.style.display = "inline-block";
  btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Executing 5-Agent Pipeline...`;

  if (liveContainer) liveContainer.style.display = "block";
  if (resultsContainer) resultsContainer.style.display = "none";

  // Step highlight helper
  const activateStep = (stepIdx) => {
    for (let i = 1; i <= 5; i++) {
      const node = document.getElementById(`wf-step-${i}`);
      if (node) {
        if (i < stepIdx) {
          node.className = "step-node completed";
        } else if (i === stepIdx) {
          node.className = "step-node active";
        } else {
          node.className = "step-node";
        }
      }
    }
  };

  try {
    activateStep(1);
    await new Promise(r => setTimeout(r, 400));
    activateStep(2);
    await new Promise(r => setTimeout(r, 400));
    activateStep(3);

    const response = await fetch(`/api/tickets/${ticketId}/run-agents`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || "Failed to execute multi-agent workflow");
    }

    activateStep(4);
    await new Promise(r => setTimeout(r, 400));
    activateStep(5);

    // Refresh page to show updated SQLite persistence and rendered output
    setTimeout(() => {
      window.location.reload();
    }, 600);

  } catch (error) {
    console.error("Multi-Agent Error:", error);
    alert(`Error executing multi-agent pipeline: ${error.message}`);
    btn.disabled = false;
    btn.innerHTML = `⚡ Run Multi-Agent Resolution`;
  }
}
