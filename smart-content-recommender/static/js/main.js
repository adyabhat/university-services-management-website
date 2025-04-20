function getRecommendations() {
  const username = document.getElementById("username").value;
  const question = document.getElementById("question").value;

  if (!username || !question) {
    alert("Please enter both username and question.");
    return;
  }

  fetch('/get_recommendations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, question })
  })
  .then(res => res.json())
  .then(data => {
    const responseDiv = document.getElementById("response-content");
    if (data.response) {
      responseDiv.innerHTML = convertMarkdownToHTML(data.response);
    } else {
      responseDiv.innerText = "Something went wrong.";
    }
  });
}

function viewHistory() {
  const username = document.getElementById("username").value.trim();
  if (!username) {
    alert("Please enter your name to view history.");
    return;
  }
  window.location.href = `/history/${username}`;
}

// Utility function to convert **bold** and *bullets* to HTML
function convertMarkdownToHTML(text) {
  // Convert **bold** to <strong>
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Split into lines
  const lines = text.split('\n');
  let html = '';
  let inList = false;

  lines.forEach(line => {
    const trimmed = line.trim();

    if (trimmed.startsWith('* ')) {
      if (!inList) {
        html += '<ul>';
        inList = true;
      }
      html += `<li>${trimmed.slice(2)}</li>`;
    } else {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      if (trimmed) {
        html += `<p>${trimmed}</p>`;
      }
    }
  });

  if (inList) html += '</ul>';

  return html;
}

