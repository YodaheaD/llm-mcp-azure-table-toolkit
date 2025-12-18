import "./style.css";
import examplesData from "./QExamples.json";

const submitBtn = document.getElementById("submit") as HTMLButtonElement;
const promptInput = document.getElementById("prompt") as HTMLTextAreaElement;
const responseText = document.getElementById("response-text") as HTMLDivElement;
const responseFull = document.getElementById("response-full") as HTMLPreElement;
const viewFullResponseBtn = document.getElementById("view-full-response") as HTMLButtonElement;
const sidebar = document.getElementById('sidebar') as HTMLElement;
const toggleSidebarBtn = document.getElementById('toggle-sidebar') as HTMLButtonElement;
const examplesToggle = document.getElementById('examples-toggle') as HTMLButtonElement;
const examplesContent = document.getElementById('examples-content') as HTMLDivElement;
const examplesList = document.getElementById('examples-list') as HTMLDivElement;
const promptHistorySelect = document.getElementById('prompt-history') as HTMLSelectElement;
const seperator = document.getElementById('separator') as HTMLDivElement;
toggleSidebarBtn.addEventListener('click', () => {
  sidebar.classList.toggle('closed');
  document.body.classList.toggle('sidebar-closed');
});


// Load prompt examples
function loadExamples() {
  examplesList.innerHTML = '';
  examplesData.forEach((example, index) => {
    const exampleDiv = document.createElement('div');
    exampleDiv.className = 'example-item';
    exampleDiv.textContent = example;
    exampleDiv.addEventListener('click', () => {
      promptInput.value = example;
      // Close dropdown after selection
      examplesContent.classList.add('hidden');
      examplesToggle.textContent = 'Prompt Examples ▼';
    });
    examplesList.appendChild(exampleDiv);
  });
}

// Toggle examples dropdown
examplesToggle.addEventListener('click', () => {
  const isHidden = examplesContent.classList.contains('hidden');
  examplesContent.classList.toggle('hidden');
  examplesToggle.textContent = isHidden ? 'Prompt Examples ▲' : 'Prompt Examples ▼';
});

// Initialize examples
loadExamples();

// View full response functionality
let currentResponseData: any = null;

viewFullResponseBtn.addEventListener('click', () => {
  if (!currentResponseData) return;
  
  const newWindow = window.open('', '_blank');
  if (newWindow) {
    const responseContent = currentResponseData.response?.content
      ?.map((c: any) => c.text)
      .join('\n') || 'No response content';
    
    newWindow.document.write(responseContent);
    newWindow.document.close();
  }
});

// prompt history
function getPromptHistory(): string[] {
  const history = localStorage.getItem('promptHistory');
  return history ? JSON.parse(history) : [];
}

function savePromptToHistory(prompt: string) {
  if (!prompt.trim()) return; // Don't save empty prompts
  
  const history = getPromptHistory();
  // Remove if already exists to avoid duplicates
  const index = history.indexOf(prompt);
  if (index > -1) {
    history.splice(index, 1);
  }
  
  // Add to beginning
  history.unshift(prompt);
  
  // Keep only latest 5
  const limitedHistory = history.slice(0, 5);
  
  localStorage.setItem('promptHistory', JSON.stringify(limitedHistory));
  populatePromptHistory(); // Refresh the display
}

function populatePromptHistory() {
  const historyContainer = document.getElementById('prompt-history') as HTMLDivElement;
  const history = getPromptHistory();
  
  // Clear existing items
  historyContainer.innerHTML = '';
  
  if (history.length === 0) {
    const emptyMessage = document.createElement('div');
    emptyMessage.textContent = 'No history yet';
    emptyMessage.style.color = '#9ca3af';
    emptyMessage.style.fontStyle = 'italic';
    emptyMessage.style.padding = '0.5rem';
    historyContainer.appendChild(emptyMessage);
    return;
  }
  
  history.forEach((prompt, index) => {
    const historyItem = document.createElement('div');
    historyItem.className = 'history-item';
    // Truncate long prompts for display
    const displayText = prompt.length > 50 ? prompt.substring(0, 50) + '...' : prompt;
    historyItem.textContent = displayText;
    historyItem.title = prompt; // Show full text on hover
    historyItem.style.cursor = 'pointer';
    historyItem.addEventListener('click', () => {
      promptInput.value = prompt;
    });
    historyContainer.appendChild(historyItem);
  });
}
populatePromptHistory();


submitBtn.addEventListener("click", async () => {
  const prompt = promptInput.value;
  responseText.textContent = "Loading...";
  responseFull.textContent = "";
  responseFull.classList.add("hidden");
  viewFullResponseBtn.classList.add("hidden");
  currentResponseData = null;

  // Save prompt to history before making the request
  savePromptToHistory(prompt);

  try {
    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input: prompt }),
    });

    const data = await res.json();
    currentResponseData = data;

    // Show only the main text in the div
    if (data.response?.content?.length > 0) {
      responseText.textContent = data.response.content
        .map((c: any) => c.text)
        .join("\n");
      responseFull.textContent = JSON.stringify(data, null, 2);
      viewFullResponseBtn.classList.remove("hidden"); // Show the button for valid responses
    } else {
      responseText.textContent = "No response content.";
      responseFull.textContent = JSON.stringify(data, null, 2);
    }
  } catch (err) {
    responseText.textContent = "Error fetching response.";
    responseFull.textContent = String(err);
  }
});

// Toggle full response on click
responseText.addEventListener("click", () => {
  responseFull.classList.toggle("hidden");
});
