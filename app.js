// RetroStories Application Logic

// GitHub Repository Configuration (Update this for your site!)
const GITHUB_CONFIG = {
  username: "worstcod", // Replace with your GitHub Username
  repo: "stories.github.io"        // Replace with your repository name
};

// Web3Forms Access Key for direct background email submission
// (Go to https://web3forms.com/ to get a free Access Key for your email address)
const WEB3FORMS_ACCESS_KEY = "67175eb2-6218-4080-94db-64f039419675";

// State Management
let state = {
  activeStoryId: null,
  activeCategory: "all", // "all", "Zen", "Wisdom", "Parable", "Fable", "Humor"
  searchQuery: "",
  readStories: [],
  theme: "light", // "light", "inverted"
  fontStyle: "serif", // "serif", "mono"
  expandedAuthors: {} // Tracks which accordions are open
};

// Initialize the Application
document.addEventListener("DOMContentLoaded", () => {
  loadStateFromLocalStorage();
  initThemeAndFont();
  initFontCycle(); // New: cycle fonts button
  initCategoryTabs();
  initSidebar();
  initSubmissionForm();
  initNotifications();
  initSwipeGestures();
  initSourcesOverlay();
  
  // Set initial layout
  renderAccordionIndex();
  
  // Load default story or show placeholder
  const urlParams = new URLSearchParams(window.location.search);
  const storyIdFromUrl = urlParams.get("story");
  if (storyIdFromUrl && STORIES_INDEX.some(s => s.id === storyIdFromUrl)) {
    loadStory(storyIdFromUrl);
  } else if (STORIES_INDEX.length > 0) {
    // Load first story in list
    loadStory(STORIES_INDEX[0].id);
  } else {
    showPlaceholder();
  }
});

// --- Theme & Font Settings ---
function loadStateFromLocalStorage() {
  if (localStorage.getItem("retro_theme")) {
    state.theme = localStorage.getItem("retro_theme");
  }
  if (localStorage.getItem("retro_font")) {
    state.fontStyle = localStorage.getItem("retro_font");
  }
  if (localStorage.getItem("retro_read_stories")) {
    try {
      state.readStories = JSON.parse(localStorage.getItem("retro_read_stories"));
    } catch (e) {
      state.readStories = [];
    }
  }
}

function initThemeAndFont() {
  const body = document.body;
  const themeToggle = document.getElementById("theme-toggle");
  
  // Apply initial theme
  if (state.theme === "inverted") {
    body.classList.add("inverted-mode");
    themeToggle.textContent = "[ LIGHT MODE ]";
  } else {
    body.classList.remove("inverted-mode");
    themeToggle.textContent = "[ DARK MODE ]";
  }
  
  // Apply initial font
  updateActiveFont();

  // Listeners
  themeToggle.addEventListener("click", () => {
    if (state.theme === "light") {
      state.theme = "inverted";
      body.classList.add("inverted-mode");
      themeToggle.textContent = "[ LIGHT MODE ]";
    } else {
      state.theme = "light";
      body.classList.remove("inverted-mode");
      themeToggle.textContent = "[ DARK MODE ]";
    }
    localStorage.setItem("retro_theme", state.theme);
    showToast(`Theme set to ${state.theme} contrast`);
  });
}

function initFontCycle() {
  const cycleBtn = document.getElementById("font-cycle-btn");
  if (!cycleBtn) return;
  
  // Initialize button text
  cycleBtn.textContent = `[ ${state.fontStyle.toUpperCase()} ]`;
  
  const fonts = ["serif", "sans", "mono"];
  cycleBtn.addEventListener("click", () => {
    const currentIdx = fonts.indexOf(state.fontStyle);
    const nextIdx = (currentIdx + 1) % fonts.length;
    state.fontStyle = fonts[nextIdx];
    cycleBtn.textContent = `[ ${state.fontStyle.toUpperCase()} ]`;
    updateActiveFont();
    localStorage.setItem("retro_font", state.fontStyle);
    showToast(`Font switched to ${state.fontStyle}`);
  });
}

function updateActiveFont() {
  const root = document.documentElement;
  if (state.fontStyle === "serif") {
    root.style.setProperty("--font-active-reading", "var(--font-reading-serif)");
  } else if (state.fontStyle === "sans") {
    root.style.setProperty("--font-active-reading", "var(--font-reading-sans)");
  } else {
    root.style.setProperty("--font-active-reading", "var(--font-reading-mono)");
  }
}

// --- Category Tabs Navigation ---
function initCategoryTabs() {
  const tabs = document.querySelectorAll(".cat-tab");
  const randomBtn = document.getElementById("random-story-btn");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      // Remove active from all tabs
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      // Update state and list
      state.activeCategory = tab.dataset.category;
      renderAccordionIndex();
      showToast(`Category set to: ${tab.dataset.category.toUpperCase()}`);
    });
  });

  randomBtn.addEventListener("click", () => {
    readRandomStory();
  });
}

// --- Sidebar Search & Accordion ---
function initSidebar() {
  const searchBox = document.getElementById("search-box");
  const sidebarToggle = document.getElementById("mobile-sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  let debounceTimer;
  
  // Search box input with debounce
  searchBox.addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      state.searchQuery = e.target.value.toLowerCase();
      renderAccordionIndex();
    }, 300);
  });

  // Mobile drawer toggle
  sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("mobile-open");
    if (sidebar.classList.contains("mobile-open")) {
      sidebarToggle.textContent = "[ CLOSE INDEX ]";
    } else {
      sidebarToggle.textContent = "[ OPEN INDEX ]";
    }
  });
}

// Helper to filter stories by search query & category
function getFilteredStories() {
  return STORIES_INDEX.filter(story => {
    const wordCount = story.content.trim().split(/\s+/).filter(Boolean).length;
    let category = story.category || (wordCount < 150 ? "flash" : wordCount <= 500 ? "mid" : "deep");
    category = category.toLowerCase();

    // Category match
    const matchesCategory = state.activeCategory === "all" || 
      category === state.activeCategory.toLowerCase();
    
    // Search match
    const matchesSearch = story.title.toLowerCase().includes(state.searchQuery) ||
      story.author.toLowerCase().includes(state.searchQuery) ||
      category.includes(state.searchQuery) ||
      story.content.toLowerCase().includes(state.searchQuery);

    return matchesCategory && matchesSearch;
  });
}

// Render the sidebar accordion list dynamically
function renderAccordionIndex() {
  const container = document.getElementById("accordion-list");
  container.innerHTML = "";
  
  const filteredStories = getFilteredStories();
  
  // Group stories by author
  const authorGroups = {};
  filteredStories.forEach(story => {
    if (!authorGroups[story.author]) {
      authorGroups[story.author] = [];
    }
    authorGroups[story.author].push(story);
  });
  
  const authors = Object.keys(authorGroups).sort();
  
  if (authors.length === 0) {
    container.innerHTML = `<p style="padding: 1.5rem; text-align: center; opacity: 0.6; font-size: 0.85rem;">No stories match current filters</p>`;
    return;
  }
  
  authors.forEach(author => {
    const authorStories = authorGroups[author];
    const itemDiv = document.createElement("div");
    itemDiv.className = "accordion-item";
    
    // Check if search query is active to auto-expand
    const isSearching = state.searchQuery.length > 0;
    const isExpanded = isSearching || state.expandedAuthors[author];
    
    if (isExpanded) {
      itemDiv.classList.add("active");
    }
    
    // Header
    const headerBtn = document.createElement("button");
    headerBtn.className = "accordion-header";
    headerBtn.innerHTML = `
      <span>${author.toUpperCase()} (${authorStories.length})</span>
      <span class="accordion-icon">${isExpanded ? "−" : "+"}</span>
    `;
    
    // Content story list
    const contentUl = document.createElement("ul");
    contentUl.className = "accordion-content";
    
    authorStories.forEach(story => {
      const isRead = state.readStories.includes(story.id);
      const isActive = story.id === state.activeStoryId;
      
      const wordCount = story.content.trim().split(/\s+/).filter(Boolean).length;
      const readTime = Math.max(1, Math.ceil(wordCount / 200));

      const li = document.createElement("li");
      li.className = `accordion-story-link ${isActive ? "active" : ""}`;
      li.innerHTML = `
        <span>${story.title}<span class="sidebar-read-time">(${readTime}m)</span></span>
        <span class="story-read-mark">${isRead ? "✓" : ""}</span>
      `;
      
      li.addEventListener("click", () => {
        loadStory(story.id);
        
        // Mobile auto-close drawer
        const sidebar = document.getElementById("sidebar");
        const sidebarToggle = document.getElementById("mobile-sidebar-toggle");
        if (sidebar.classList.contains("mobile-open")) {
          sidebar.classList.remove("mobile-open");
          sidebarToggle.textContent = "[ OPEN INDEX ]";
        }
      });
      
      contentUl.appendChild(li);
    });
    
    // Toggle accordion collapse
    headerBtn.addEventListener("click", () => {
      const isOpen = itemDiv.classList.toggle("active");
      state.expandedAuthors[author] = isOpen;
      headerBtn.querySelector(".accordion-icon").textContent = isOpen ? "−" : "+";
    });
    
    itemDiv.appendChild(headerBtn);
    itemDiv.appendChild(contentUl);
    container.appendChild(itemDiv);
  });
}

// --- Story Reader ---
function showPlaceholder() {
  const pane = document.getElementById("reading-pane");
  pane.innerHTML = `
    <div class="story-placeholder">
      <h2>NO STORY LOADED</h2>
      <p>Select a story from the index or click the random button above to start reading.</p>
    </div>
  `;
}

function loadStory(storyId) {
  state.activeStoryId = storyId;

  // Retrieve story directly from preloaded STORIES_INDEX array (NO FETCH / CORS errors!)
  const storyObj = STORIES_INDEX.find(s => s.id === storyId);
  if (!storyObj) {
    showPlaceholder();
    return;
  }

  const wordCount = storyObj.content.trim().split(/\s+/).filter(Boolean).length;
  const readTime = Math.max(1, Math.ceil(wordCount / 200));

  // Set the reading panel content
  const pane = document.getElementById("reading-pane");
  pane.innerHTML = `
    <div class="reading-content-wrapper">
      <div class="story-meta">
        <h2>${storyObj.title}</h2>
        <div class="story-details">
          <span>By: ${storyObj.author}</span>
          <span>•</span>
          <span>🕒 ${readTime} min read</span>
          <span>•</span>
          <span>${wordCount} words</span>
        </div>
      </div>
      <div class="story-body" id="story-text-body"></div>
      
      <!-- Story Navigation Buttons -->
      <div class="story-navigation">
        <button class="pixel-btn" id="prev-story-btn">[ PREVIOUS STORY ]</button>
        <button class="pixel-btn" id="next-story-btn">[ NEXT STORY ]</button>
        <button class="pixel-btn" id="share-story-btn">[ SHARE STORY ]</button>
      </div>
    </div>
  `;

  // Render the preloaded story content instantly
  document.getElementById("story-text-body").textContent = storyObj.content;
  
  // Bind navigation and share buttons
  const prevBtn = document.getElementById("prev-story-btn");
  const nextBtn = document.getElementById("next-story-btn");
  const shareBtn = document.getElementById("share-story-btn");

  if (prevBtn && nextBtn) {
    const currentFiltered = getFilteredStories();
    const currentIndex = currentFiltered.findIndex(s => s.id === storyId);

    if (currentFiltered.length <= 1) {
      prevBtn.style.display = "none";
      nextBtn.style.display = "none";
    } else {
      prevBtn.addEventListener("click", () => {
        const prevIdx = (currentIndex - 1 + currentFiltered.length) % currentFiltered.length;
        loadStory(currentFiltered[prevIdx].id);
      });
      nextBtn.addEventListener("click", () => {
        const nextIdx = (currentIndex + 1) % currentFiltered.length;
        loadStory(currentFiltered[nextIdx].id);
      });
    }
  }

  // Share button handling
  if (shareBtn) {
    shareBtn.addEventListener("click", () => {
      const shareUrl = `${window.location.origin}${window.location.pathname}?story=${storyObj.id}`;
      const shareData = {
        title: storyObj.title,
        text: storyObj.content.substring(0, 200) + "...",
        url: shareUrl
      };
      if (navigator.share) {
        navigator.share(shareData).catch(err => {
          console.error(err);
          showToast("Sharing failed");
        });
      } else {
        navigator.clipboard.writeText(shareUrl).then(() => {
          showToast("Story link copied to clipboard");
        }).catch(() => {
          showToast("Copy to clipboard failed");
        });
      }
    });
  }
  markStoryAsRead(storyId);
  
  // Auto-scroll pane to top
  pane.scrollTop = 0;

  // Keep accordion parent expanded for loaded story
  state.expandedAuthors[storyObj.author] = true;

  // Re-render sidebar to update active item highlights and read checkmarks
  renderAccordionIndex();
}

function markStoryAsRead(storyId) {
  if (!state.readStories.includes(storyId)) {
    state.readStories.push(storyId);
    localStorage.setItem("retro_read_stories", JSON.stringify(state.readStories));
  }
}

// --- Non-Repeating Randomizer ---
function readRandomStory() {
  const filtered = getFilteredStories();
  
  if (filtered.length === 0) {
    showToast("No stories available in this category!");
    return;
  }

  // Find unread stories in the active category
  let unread = filtered.filter(story => !state.readStories.includes(story.id));

  // If all stories are read, reset history for the filtered category
  if (unread.length === 0) {
    showToast("You have read all stories in this section! Resetting list...");
    
    // Remove only filtered story IDs from read storage
    const filteredIds = filtered.map(s => s.id);
    state.readStories = state.readStories.filter(id => !filteredIds.includes(id));
    localStorage.setItem("retro_read_stories", JSON.stringify(state.readStories));
    
    unread = filtered;
  }

  // Load a random story
  const randomIndex = Math.floor(Math.random() * unread.length);
  const selectedStory = unread[randomIndex];
  loadStory(selectedStory.id);
}

// --- Story Submission ---
function initSubmissionForm() {
  const modal = document.getElementById("submit-modal");
  const openBtn = document.getElementById("open-submit-btn");
  const closeBtn = document.getElementById("close-submit-btn");
  const form = document.getElementById("story-submit-form");
  const copyPreview = document.getElementById("copy-preview");
  
  openBtn.addEventListener("click", () => {
    modal.classList.add("active");
    form.reset();
    copyPreview.style.display = "none";
  });

  closeBtn.addEventListener("click", () => {
    modal.classList.remove("active");
  });

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.classList.remove("active");
    }
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    
    const title = document.getElementById("story-title").value.trim();
    const author = document.getElementById("story-author").value;
    const customAuthor = document.getElementById("story-author-custom").value.trim();
    const content = document.getElementById("story-content").value.trim();
    
    const finalAuthor = author === "Other" ? customAuthor : author;
    
    if (!title || !finalAuthor || !content) {
      alert("Please fill all required fields!");
      return;
    }
    
    // Auto-calculate category based on content word count
    const wordCount = content.split(/\s+/).filter(Boolean).length;
    let autoCategory = "mid";
    if (wordCount < 150) {
      autoCategory = "flash";
    } else if (wordCount > 500) {
      autoCategory = "deep";
    }
    
    // Generate simple ID
    const storyId = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
    
    // Format JSON configuration entry
    const jsonEntry = {
      id: storyId,
      title: title,
      author: finalAuthor,
      category: autoCategory,
      content: content
    };
    
    // Target author script file suggestion
    const filename = finalAuthor.toLowerCase().includes("osho") ? "osho.js" :
                     finalAuthor.toLowerCase().includes("zen") ? "zen.js" :
                     finalAuthor.toLowerCase().includes("sadhguru") ? "sadhguru.js" :
                     finalAuthor.toLowerCase().includes("aesop") ? "aesop.js" :
                     finalAuthor.toLowerCase().includes("krishnamurti") || finalAuthor.toLowerCase().includes("jk") ? "jk.js" : "custom.js";

    const formattedCode = `// Copy and add this block inside the square brackets [ ... ] of stories/${filename}:\n{\n  "id": "${storyId}",\n  "title": "${title}",\n  "author": "${finalAuthor}",\n  "category": "${autoCategory}",\n  "content": \`${content.replace(/`/g, '\\`').replace(/\${/g, '\\${')}\`\n},`;
    
    // Update copy box
    copyPreview.textContent = formattedCode;
    copyPreview.style.display = "block";
    
    // Copy to clipboard
    navigator.clipboard.writeText(formattedCode)
      .then(() => {
        showToast("Story block copied to clipboard!");
      })
      .catch(err => {
        console.error("Clipboard copy failed: ", err);
      });
      
    // Determine which button triggered submission
    const triggerBtnId = e.submitter ? e.submitter.id : "submit-btn-direct";
    
    if (triggerBtnId === "submit-btn-github") {
      // Prefill and open GitHub Issue url
      const issueTitle = encodeURIComponent(`New Story: ${title} by ${finalAuthor}`);
      const issueBody = encodeURIComponent(
        `### New Story Submission\n\n- **Title**: ${title}\n- **Author**: ${finalAuthor}\n- **Category**: ${autoCategory}\n- **Story ID**: ${storyId}\n\n#### Story Text\n\`\`\`text\n${content}\n\`\`\`\n\n#### Config Entry (Paste into stories/${filename})\n\`\`\`javascript\n{\n  id: "${storyId}",\n  title: "${title}",\n  author: "${finalAuthor}",\n  category: "${autoCategory}",\n  content: \`[Paste Text Here]\`\n},\n\`\`\``
      );
      
      const githubUrl = `https://github.com/${GITHUB_CONFIG.username}/${GITHUB_CONFIG.repo}/issues/new?title=${issueTitle}&body=${issueBody}`;
      window.open(githubUrl, "_blank");
      showToast("Redirecting to GitHub Issues...");
    } else {
      // Background POST submission to Web3Forms if Key is configured
      if (WEB3FORMS_ACCESS_KEY && WEB3FORMS_ACCESS_KEY !== "YOUR_ACCESS_KEY_HERE") {
        const submitBtn = e.submitter;
        const originalText = submitBtn.textContent;
        submitBtn.textContent = "[ SUBMITTING... ]";
        submitBtn.disabled = true;

        fetch("https://api.web3forms.com/submit", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
          },
          body: JSON.stringify({
            access_key: WEB3FORMS_ACCESS_KEY,
            subject: `New RetroStories Submission: ${title} by ${finalAuthor}`,
            from_name: "RetroStories Portal",
            title: title,
            author: finalAuthor,
            category: autoCategory,
            content: content,
            formatted_code: formattedCode
          })
        })
        .then(async (response) => {
          let json = await response.json();
          if (response.status == 200) {
            showToast("Story submitted successfully!");
            modal.classList.remove("active");
            form.reset();
          } else {
            console.error(json);
            const errMsg = json.message || "";
            if (errMsg.toLowerCase().includes("limit") || errMsg.toLowerCase().includes("exceeded") || errMsg.toLowerCase().includes("quota") || response.status == 429) {
              showToast("Direct submission limit reached!");
              alert("Notice:\nThe direct email submission limit for this month has been reached. Please submit your story directly on GitHub using the '[ SUBMIT ON GITHUB ]' button instead!");
            } else {
              showToast("Submission failed: " + (errMsg || "Unknown error"));
            }
          }
        })
        .catch(error => {
          console.error(error);
          showToast("Network error occurred during submission.");
        })
        .finally(() => {
          submitBtn.textContent = originalText;
          submitBtn.disabled = false;
        });
      } else {
        // Fallback: Prefill and open email client (obfuscated in source code to prevent bot scraping)
        const emailTo = atob("dG9iaXJhbWF0c29jaWFsbWVkaWFAZ21haWwuY29t");
        const emailSubject = encodeURIComponent(`RetroStories Submission: ${title} by ${finalAuthor}`);
        const emailBody = encodeURIComponent(
          `Hello!\n\nI would like to submit a new story to RetroStories.\n\n--- STORY DETAILS ---\nTitle: ${title}\nAuthor: ${finalAuthor}\nCategory: ${autoCategory}\n\n--- STORIES CONFIG ENTRY ---\n${formattedCode}\n\n(Note: The structured data has also been copied to your clipboard so you can easily paste it!)`
        );
        
        window.location.href = `mailto:${emailTo}?subject=${emailSubject}&body=${emailBody}`;
        showToast("Email template opened. Send it to submit!");
      }
    }
  });

  // Watch author dropdown to show custom input if 'Other' is picked
  const authorSelect = document.getElementById("story-author");
  const customAuthorGroup = document.getElementById("custom-author-group");
  
  authorSelect.addEventListener("change", (e) => {
    if (e.target.value === "Other") {
      customAuthorGroup.style.display = "block";
      document.getElementById("story-author-custom").required = true;
    } else {
      customAuthorGroup.style.display = "none";
      document.getElementById("story-author-custom").required = false;
    }
  });
}

// --- Push Notifications Simulation ---
function initNotifications() {
  const notifyBtn = document.getElementById("subscribe-notify-btn");
  const modal = document.getElementById("notify-modal");
  const closeBtn = document.getElementById("close-notify-btn");
  const testBtn = document.getElementById("test-notify-btn");
  
  notifyBtn.addEventListener("click", () => {
    if (!("Notification" in window)) {
      alert("This browser does not support desktop notifications.");
      return;
    }
    
    if (Notification.permission === "granted") {
      modal.classList.add("active");
    } else if (Notification.permission !== "denied") {
      Notification.requestPermission().then(permission => {
        if (permission === "granted") {
          modal.classList.add("active");
          showToast("Subscribed to Daily Story Notifications!");
        }
      });
    } else {
      alert("Notification access is blocked. Please enable it in browser settings.");
    }
  });

  closeBtn.addEventListener("click", () => {
    modal.classList.remove("active");
  });

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.classList.remove("active");
    }
  });

  testBtn.addEventListener("click", () => {
    triggerSimulatedNotification();
    modal.classList.remove("active");
  });
}

function triggerSimulatedNotification() {
  if (Notification.permission !== "granted") return;
  
  // Pick a random story
  const randomStory = STORIES_INDEX[Math.floor(Math.random() * STORIES_INDEX.length)];
  
  const options = {
    body: `Daily Story: "${randomStory.title}" by ${randomStory.author}. Click to open and read!`,
    tag: "daily-story",
    requireInteraction: true
  };
  
  const notification = new Notification("📜 RetroStories Daily Story", options);
  
  notification.onclick = function(event) {
    event.preventDefault();
    window.focus();
    loadStory(randomStory.id);
    notification.close();
  };

  showToast("Simulated notification sent!");
}

// --- Helper UI Utilities ---
function showToast(message) {
  let toast = document.getElementById("toast-container");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast-container";
    toast.className = "toast-msg";
    document.body.appendChild(toast);
  }
  
  toast.textContent = message;
  toast.classList.add("show");
  
  if (window.toastTimeout) {
    clearTimeout(window.toastTimeout);
  }
  
  window.toastTimeout = setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

// --- Mobile Swipe Gestures for Story Navigation ---
let touchStartX = 0;
let touchStartY = 0;
let touchEndX = 0;
let touchEndY = 0;

function initSwipeGestures() {
  const pane = document.getElementById("reading-pane");
  if (!pane) return;
  
  pane.addEventListener("touchstart", (e) => {
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
  }, { passive: true });
  
  pane.addEventListener("touchend", (e) => {
    touchEndX = e.changedTouches[0].screenX;
    touchEndY = e.changedTouches[0].screenY;
    handleSwipeGesture();
  }, { passive: true });
}

function handleSwipeGesture() {
  const diffX = touchEndX - touchStartX;
  const diffY = touchEndY - touchStartY;
  
  // Verify horizontal swipe exceeds threshold (50px) and is larger than vertical swipe
  if (Math.abs(diffX) > 50 && Math.abs(diffX) > Math.abs(diffY)) {
    const currentFiltered = getFilteredStories();
    if (currentFiltered.length <= 1) return;
    
    const currentIndex = currentFiltered.findIndex(s => s.id === state.activeStoryId);
    if (currentIndex === -1) return;
    
    if (diffX < 0) {
      // Swiped left -> load NEXT story
      const nextIdx = (currentIndex + 1) % currentFiltered.length;
      loadStory(currentFiltered[nextIdx].id);
      showToast("Next story");
    } else {
      // Swiped right -> load PREVIOUS story
      const prevIdx = (currentIndex - 1 + currentFiltered.length) % currentFiltered.length;
      loadStory(currentFiltered[prevIdx].id);
      showToast("Previous story");
    }
  }
}

// --- Sources Overlay Toggle ---
function initSourcesOverlay() {
  const overlay = document.getElementById("sources-overlay");
  const openBtn = document.getElementById("open-sources-btn");
  const closeBtn = document.getElementById("close-sources-btn");
  
  if (openBtn && overlay && closeBtn) {
    openBtn.addEventListener("click", () => {
      overlay.classList.add("active");
      showToast("Viewing Sources");
    });
    
    closeBtn.addEventListener("click", () => {
      overlay.classList.remove("active");
    });
    
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.classList.remove("active");
      }
    });
  }
}

