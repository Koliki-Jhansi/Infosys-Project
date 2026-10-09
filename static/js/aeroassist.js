/**
 * AeroAssist AI - Client Interactive Operations & Smooth Animation Controls
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('mobileSidebarToggle') || document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('appSidebar') || document.getElementById('sidebar');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== sidebarToggle) {
        sidebar.classList.remove('open');
      }
    });
  }

  // 2. Dropdown Menus
  document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
    toggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const parent = toggle.closest('.dropdown');
      if (parent) {
        // Close others
        document.querySelectorAll('.dropdown.open').forEach(d => {
          if (d !== parent) d.classList.remove('open');
        });
        parent.classList.toggle('open');
      }
    });
  });

  // Close dropdowns on outside click
  document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown.open').forEach(d => d.classList.remove('open'));
  });

  // 3. KPI Statistics Smooth Count-Up Animation (Real Database Values Only)
  const kpiValues = document.querySelectorAll('.kpi-value');
  kpiValues.forEach(el => {
    const rawText = el.innerText.trim();
    const targetNum = parseInt(rawText, 10);
    if (!isNaN(targetNum) && targetNum > 0) {
      const duration = 800; // ms
      const startTime = performance.now();
      
      const step = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Easing: easeOutQuad
        const easeProgress = 1 - (1 - progress) * (1 - progress);
        const currentVal = Math.floor(easeProgress * targetNum);
        el.innerText = currentVal;
        
        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          el.innerText = targetNum;
        }
      };
      requestAnimationFrame(step);
    }
  });

  // 4. Form Submission Loading States (Login, Register, Ticket Create)
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        // Save current text
        const originalText = submitBtn.innerHTML;
        // Don't modify if it's GET filter form
        if (form.method.toUpperCase() === 'POST') {
          setTimeout(() => {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
              <span style="display:inline-block; width:14px; height:14px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite; margin-right:8px; vertical-align:middle;"></span>
              Processing...
            `;
          }, 20);
        }
      }
    });
  });

  // 5. Multi-Agent Run Trigger (Executes existing orchestrator exactly once per click)
  const runAgentsBtn = document.getElementById('runAgentsBtn');
  if (runAgentsBtn) {
    runAgentsBtn.addEventListener('click', async () => {
      const ticketId = runAgentsBtn.getAttribute('data-ticket-id');
      if (!ticketId) {
        alert('Please select a ticket first.');
        return;
      }

      runAgentsBtn.disabled = true;
      runAgentsBtn.innerHTML = `
        <span class="spinner" style="display:inline-block; width:16px; height:16px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite; margin-right:6px;"></span>
        Executing Five Agents...
      `;

      // Highlight stepper with animated pulse
      const activeStep = document.querySelector('.stepper-step.active .step-bubble');
      if (activeStep) {
        activeStep.style.animation = 'pulseActiveStep 0.8s infinite';
      }

      try {
        const response = await fetch(`/api/tickets/${ticketId}/run-agents`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        if (data.success) {
          // Reload page to display the freshly persisted AI resolution & audit trace
          window.location.reload();
        } else {
          alert('Agent execution failed: ' + (data.error || 'Unknown error'));
          runAgentsBtn.disabled = false;
          runAgentsBtn.innerHTML = '<span>⚡</span> Run AI Resolution';
        }
      } catch (err) {
        console.error('Error running agents:', err);
        alert('An unexpected error occurred during execution.');
        runAgentsBtn.disabled = false;
        runAgentsBtn.innerHTML = '<span>⚡</span> Run AI Resolution';
      }
    });
  }

  // 6. Live RAG Preview on Ticket Create Form
  const descInput = document.getElementById('ticketDescription');
  const titleInput = document.getElementById('ticketTitle');
  const ragPreviewContainer = document.getElementById('createRagPreview');

  let debounceTimer;
  function updateLivePreview() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      const title = titleInput ? titleInput.value.trim() : '';
      const description = descInput ? descInput.value.trim() : '';

      if ((title.length > 5 || description.length > 10) && ragPreviewContainer) {
        try {
          const res = await fetch('/api/rag/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description })
          });
          const data = await res.json();
          if (data && data.knowledge_found && data.top_article) {
            ragPreviewContainer.style.display = 'block';
            ragPreviewContainer.style.animation = 'scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
            ragPreviewContainer.innerHTML = `
              <div style="font-size:0.8rem; color:#38BDF8; font-weight:700; margin-bottom:0.25rem;">
                🎯 AI Knowledge Match Preview (${(data.similarity_score * 100).toFixed(1)}% match):
              </div>
              <div style="font-size:0.85rem; color:#fff; font-weight:600;">${data.top_article.title}</div>
              <div style="font-size:0.75rem; color:#94A3B8; margin-top:0.2rem;">${data.top_article.content.substring(0, 160)}...</div>
            `;
          } else if (ragPreviewContainer) {
            ragPreviewContainer.style.display = 'none';
          }
        } catch (e) {
          // Silently pass
        }
      }
    }, 400);
  }

  if (titleInput) titleInput.addEventListener('input', updateLivePreview);
  if (descInput) descInput.addEventListener('input', updateLivePreview);

  // 7. Scroll Animation Observer for Feature & Card Elements
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.feature-card, .card-panel, .kpi-card').forEach(el => {
      observer.observe(el);
    });
  }
});
