import json
import requests
import re
import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS # Required for cross-origin requests from frontend

app = Flask(__name__)
CORS(app) # Enable CORS for frontend requests

# Define a simple knowledge graph for demonstration
# In a real application, this would be much larger and loaded from a database
KNOWLEDGE_GRAPH = {
    "Introduction to ML": {
        "prerequisites": [],
        "resources": [
            {"type": "video", "title": "Machine Learning Full Course - Edureka", "url": "https://www.youtube.com/watch?v=GwIo3gDZCVQ"},
            {"type": "article", "title": "What is Machine Learning?", "url": "https://www.ibm.com/topics/machine-learning"}
        ]
    },
    "Supervised Learning": {
        "prerequisites": ["Introduction to ML"],
        "resources": [
            {"type": "video", "title": "Supervised Learning - StatQuest", "url": "https://www.youtube.com/watch?v=5qv5w0Xl5XA"},
            {"type": "article", "title": "Supervised Learning Overview (Wikipedia)", "url": "https://en.wikipedia.org/wiki/Supervised_learning"}
        ]
    },
    "Unsupervised Learning": {
        "prerequisites": ["Introduction to ML"],
        "resources": [
            { 
                "type": "video", 
                "title": "Unsupervised Learning - Simplilearn", 
                "url": "https://www.youtube.com/watch?v=3g6h4cS2h0Q" 
            },
            { 
                "type": "article", 
                "title": "Unsupervised Learning Explained", 
                "url": "https://www.geeksforgeeks.org/unsupervised-learning/" 
            }
        ]
    },
    "Deep Learning Basics": {
        "prerequisites": ["Supervised Learning", "Unsupervised Learning"],
        "resources": [
            {"type": "video", "title": "Deep Learning Fundamentals - Simplilearn", "url": "https://www.youtube.com/watch?v=aircAruvnKk"},
            {"type": "article", "title": "Introduction to Deep Learning", "url": "https://www.ibm.com/topics/deep-learning"}
        ]
    },
    "Natural Language Processing (NLP)": {
        "prerequisites": ["Deep Learning Basics"],
        "resources": [
            {"type": "video", "title": "NLP Full Course - Simplilearn", "url": "https://www.youtube.com/watch?v=8u6aF4Lw2xw"},
            {"type": "article", "title": "NLP Guide by Google", "url": "https://developers.google.com/machine-learning/guides/text-classification/step-2"}
        ]
    },
    "Computer Vision (CV)": {
        "prerequisites": ["Deep Learning Basics"],
        "resources": [
            {"type": "video", "title": "Computer Vision Full Course - Edureka", "url": "https://www.youtube.com/watch?v=5rC7b-HB1Vg"},
            {"type": "article", "title": "A Beginner’s Guide to Computer Vision", "url": "https://www.analyticsvidhya.com/blog/2021/06/computer-vision-an-introduction/"}
        ]
    },
    "Reinforcement Learning": {
        "prerequisites": ["Introduction to ML"],
        "resources": [
            {"type": "video", "title": "Reinforcement Learning - StatQuest", "url": "https://www.youtube.com/watch?v=2pWv7GOvuf0"},
            {"type": "article", "title": "Reinforcement Learning: An Introduction", "url": "https://www.oreilly.com/library/view/reinforcement-learning-an/9780137460880/"}
        ]
    },
    "MLOps Fundamentals": {
        "prerequisites": ["Introduction to ML"],
        "resources": [
            {"type": "video", "title": "MLOps Tutorial for Beginners - Simplilearn", "url": "https://www.youtube.com/watch?v=06-AZXmwHjo"},
            {"type": "article", "title": "What is MLOps?", "url": "https://azure.microsoft.com/en-us/resources/cloud-computing-dictionary/what-is-mlops/"}
        ]
    }
}

DYNAMIC_KNOWLEDGE_GRAPH = None  # Add this global variable at the top

def call_gemini_for_rich_kg():
    """
    Calls Gemini to generate a rich knowledge graph for ML topics.
    """
    prompt = (
        "Generate a comprehensive JSON knowledge graph for machine learning education. "
        "For each concept, include: "
        "- prerequisites (list of concept names), "
        "- at least 3 real, high-quality video courses (with title and URL) from reputable platforms (Coursera, edX, YouTube, DeepLearning.AI, MIT, Stanford, etc.), "
        "- at least 2 in-depth articles (with title and URL) from trusted sources, "
        "- at least 1 recommended book (with title and URL), "
        "- at least 1 MOOC (with title and URL, if available). "
        "The output should be a JSON object with concept names as keys and the above fields as values. "
        "**Only include real, existing resources with accurate URLs. Do not invent or hallucinate resources.**"
    )
    api_key = "AIzaSyDoCNYecUmxS4FkwRvr7ESnQWL7Ju8QxI0"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
        response.raise_for_status()
        result = response.json()
        print("========== Gemini Full API Response ==========")
        print(json.dumps(result, indent=2))
        print("==============================================")
        # Try to extract JSON from Gemini's response
        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
            raw_llm_response = result['candidates'][0]['content']['parts'][0]['text']
            print("========== Gemini Raw Output ==========")
            print(raw_llm_response)
            print("=======================================")
            match = re.search(r'```json\n(.*)\n```', raw_llm_response, re.DOTALL)
            if match:
                json_string = match.group(1)
            else:
                json_string = raw_llm_response
            kg = json.loads(json_string)
            return kg
        else:
            print("Gemini KG: Unexpected response structure.")
            return None
    except Exception as e:
        print(f"Gemini KG API failed: {e}")
        return None

@app.route('/generate_knowledge_graph', methods=['POST'])
def generate_knowledge_graph():
    """
    Calls Gemini to generate a rich knowledge graph and updates the global DYNAMIC_KNOWLEDGE_GRAPH.
    """
    global DYNAMIC_KNOWLEDGE_GRAPH
    kg = call_gemini_for_rich_kg()
    if kg:
        DYNAMIC_KNOWLEDGE_GRAPH = kg
        return jsonify({"status": "success", "knowledge_graph": DYNAMIC_KNOWLEDGE_GRAPH})
    else:
        return jsonify({"status": "error", "message": "Failed to generate knowledge graph"}), 500

def call_gemini_api(prompt_text: str) -> dict:
    """
    Calls the Gemini AI model with the given prompt.
    """
    chat_history = [{"role": "user", "parts": [{"text": prompt_text}]}]

    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "path": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["path"]
            }
        }
    }

    # In a real application, you would get the API key securely, e.g., from environment variables
    # For Canvas environment, an empty string allows the runtime to inject it.
    api_key = "AIzaSyDoCNYecUmxS4FkwRvr7ESnQWL7Ju8QxI0"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    try:
        print("Hello Gemini API, here is my prompt:")
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
        response.raise_for_status()
        result = response.json()
        print("========== Gemini Full API Response ==========")
        print(json.dumps(result, indent=2))
        print("==============================================")
        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
            raw_llm_response = result['candidates'][0]['content']['parts'][0]['text']
            print(f"Raw LLM Response: {raw_llm_response}")

            match = re.search(r'```json\n(.*)\n```', raw_llm_response, re.DOTALL)
            if match:
                json_string = match.group(1)
            else:
                json_string = raw_llm_response

            parsed_result = json.loads(json_string)
            return parsed_result
        else:
            print(f"Unexpected API response structure: {result}")
            return {"path": []}
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return {"path": []}
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}. Raw response: {json_string if 'json_string' in locals() else raw_llm_response}")
        return {"path": []}
    except Exception as e:
        print(f"An unexpected error occurred during API call: {e}")
        return {"path": []}

@app.route('/')
def index():
    """Serves the main HTML page."""
    # This is where you would typically render an HTML template from a 'templates' folder.
    # For simplicity in Canvas, we'll render the HTML string directly.
    # In a real project, you'd have your HTML file in a 'templates' directory
    # and use render_template('index.html').
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Personalized ML Learning Path</title>
        <!-- Tailwind CSS CDN -->
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {
                font-family: 'Inter', sans-serif;
                background-color: #f0f4f8; /* Light blue-gray background */
            }
            /* Custom scrollbar for better aesthetics */
            ::-webkit-scrollbar {
                width: 8px;
            }
            ::-webkit-scrollbar-track {
                background: #e2e8f0; /* Light gray track */
                border-radius: 10px;
            }
            ::-webkit-scrollbar-thumb {
                background: #a78bfa; /* Purple thumb */
                border-radius: 10px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #8b5cf6; /* Darker purple on hover */
            }
        </style>
    </head>
    <body class="min-h-screen bg-gradient-to-br from-blue-50 to-purple-100 p-4 sm:p-8 text-gray-800">
        <div class="max-w-4xl mx-auto bg-white rounded-xl shadow-2xl overflow-hidden border border-purple-200">
            <header class="bg-gradient-to-r from-purple-700 to-indigo-800 text-white p-6 sm:p-8">
                <h1 class="text-3xl sm:text-4xl font-extrabold mb-2 text-center tracking-tight">Personalized ML Learning Path</h1>
                <p class="text-purple-200 text-center text-lg">Your AI-powered guide to mastering Machine Learning concepts.</p>
            </header>

            <main class="p-6 sm:p-8">
                <!-- Goal Input Section -->
                <div class="mb-8 p-6 bg-indigo-50 border border-indigo-200 rounded-lg shadow-inner">
                    <label for="goalInput" class="block text-lg font-semibold text-indigo-800 mb-2">
                        What is your learning goal?
                    </label>
                    <input
                        type="text"
                        id="goalInput"
                        placeholder="e.g., 'Understand Deep Learning for NLP' or 'MLOps Fundamentals'"
                        class="w-full p-3 border border-indigo-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200 text-gray-700"
                    />
                    <button
                        id="generatePathBtn"
                        class="mt-4 w-full sm:w-auto px-6 py-3 rounded-lg font-semibold text-white transition duration-300 ease-in-out bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 shadow-md hover:shadow-lg"
                    >
                        Generate My Path
                    </button>
                </div>

                <!-- Messages/Loading/Error Display -->
                <div id="messageDisplay" class="mb-4"></div>
                <div id="errorDisplay" class="mb-4 text-red-700 font-medium"></div>
                <div id="loadingIndicator" class="hidden flex justify-center items-center py-8">
                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
                    <p class="ml-4 text-purple-600 text-lg">Thinking...</p>
                </div>

                <!-- Learning Path Display Section -->
                <section id="learningPathSection" class="mt-8 hidden">
                    <h2 class="text-2xl font-bold text-gray-700 mb-6 border-b-2 border-purple-300 pb-2">Your Personalized Learning Path</h2>
                    <ol id="learningPathList" class="space-y-6"></ol>
                </section>

                <!-- Current Knowledge State Section -->
                <section class="mt-12 p-6 bg-gray-50 border border-gray-200 rounded-lg shadow-inner">
                    <h2 class="text-xl font-bold text-gray-700 mb-4">Your Current Knowledge State</h2>
                    <div class="flex flex-wrap gap-4">
                        <div class="flex-1 min-w-[200px]">
                            <h3 class="font-semibold text-green-700 mb-2">Known Concepts:</h3>
                            <ul id="knownConceptsList" class="list-disc list-inside text-gray-600">
                                <li class="italic text-gray-500">No concepts marked as known yet.</li>
                            </ul>
                        </div>
                        <div class="flex-1 min-w-[200px]">
                            <h3 class="font-semibold text-yellow-700 mb-2">Struggling Concepts:</h3>
                            <ul id="strugglingConceptsList" class="list-disc list-inside text-gray-600">
                                <li class="italic text-gray-500">No concepts marked as struggling yet.</li>
                            </ul>
                        </div>
                    </div>
                    <button
                        id="resetAllBtn"
                        class="mt-6 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors duration-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                    >
                        Reset All
                    </button>
                </section>
            </main>
        </div>

        <script>
            // Define a simple knowledge graph (same as Python for consistency)
            const KNOWLEDGE_GRAPH = {
                "Introduction to ML": {
                    prerequisites: [],
                    resources: [
                        { type: "video", title: "Machine Learning Full Course - Edureka", url: "https://www.youtube.com/watch?v=GwIo3gDZCVQ" },
                        { type: "article", title: "What is Machine Learning?", url: "https://www.ibm.com/topics/machine-learning" }
                    ]
                },
                "Supervised Learning": {
                    prerequisites: ["Introduction to ML"],
                    resources: [
                        { type: "video", title: "Supervised Learning - StatQuest", url: "https://www.youtube.com/watch?v=5qv5w0Xl5XA" },
                        { type: "article", title: "Supervised Learning Overview (Wikipedia)", url: "https://en.wikipedia.org/wiki/Supervised_learning" }
                    ]
                },
                "Unsupervised Learning": {
                    prerequisites: ["Introduction to ML"],
                    resources: [
                        { 
                            type: "video", 
                            title: "Unsupervised Machine Learning for Beginners", 
                            url: "https://www.youtube.com/watch?v=yteYU_QpUxs" 
                        },
                        { 
                            type: "article", 
                            title: "Unsupervised Learning Explained", 
                            url: "https://www.geeksforgeeks.org/unsupervised-learning/" 
                        }
                    ]
                },
                "Deep Learning Basics": {
                    prerequisites: ["Supervised Learning", "Unsupervised Learning"],
                    resources: [
                        { type: "video", title: "Deep Learning Fundamentals - Simplilearn", url: "https://www.youtube.com/watch?v=aircAruvnKk" },
                        { type: "article", title: "Introduction to Deep Learning", url: "https://www.ibm.com/topics/deep-learning" }
                    ]
                },
                "Natural Language Processing (NLP)": {
                    prerequisites: ["Deep Learning Basics"],
                    resources: [
                        { type: "video", title: "NLP Full Course - Simplilearn", url: "https://www.youtube.com/watch?v=8u6aF4Lw2xw" },
                        { type: "article", title: "NLP Guide by Google", url: "https://developers.google.com/machine-learning/guides/text-classification/step-2" }
                    ]
                },
                "Computer Vision (CV)": {
                    prerequisites: ["Deep Learning Basics"],
                    resources: [
                        { type: "video", title: "Computer Vision Full Course - Edureka", url: "https://www.youtube.com/watch?v=5rC7b-HB1Vg" },
                        { type: "article", title: "A Beginner’s Guide to Computer Vision", url: "https://www.analyticsvidhya.com/blog/2021/06/computer-vision-an-introduction/" }
                    ]
                },
                "Reinforcement Learning": {
                    prerequisites: ["Introduction to ML"],
                    resources: [
                        { type: "video", title: "Reinforcement Learning - StatQuest", url: "https://www.youtube.com/watch?v=2pWv7GOvuf0" },
                        { type: "article", title: "Reinforcement Learning: An Introduction", url: "https://medium.com/analytics-vidhya/a-beginners-guide-to-reinforcement-learning-and-its-basic-implementation-from-scratch-2c0b5444cc49" }
                    ]
                },
                "MLOps Fundamentals": {
                    prerequisites: ["Introduction to ML"],
                    resources: [
                        { type: "video", title: "MLOps Tutorial for Beginners - Simplilearn", url: "https://www.youtube.com/watch?v=06-AZXmwHjo" },
                        { type: "article", title: "What is MLOps?", url: "https://azure.microsoft.com/en-us/resources/cloud-computing-dictionary/what-is-mlops/" }
                    ]
                }
            };

            // State variables (simulating React's useState)
            let goal = '';
            let userKnownConcepts = new Set();
            let userStrugglingConcepts = new Set();
            let learningPath = [];
            let loading = false;

            // DOM Elements
            const goalInput = document.getElementById('goalInput');
            const generatePathBtn = document.getElementById('generatePathBtn');
            const messageDisplay = document.getElementById('messageDisplay');
            const errorDisplay = document.getElementById('errorDisplay');
            const loadingIndicator = document.getElementById('loadingIndicator');
            const learningPathSection = document.getElementById('learningPathSection');
            const learningPathList = document.getElementById('learningPathList');
            const knownConceptsList = document.getElementById('knownConceptsList');
            const strugglingConceptsList = document.getElementById('strugglingConceptsList');
            const resetAllBtn = document.getElementById('resetAllBtn');

            // --- UI Update Functions ---
            function updateUI() {
                // Update goal input
                goalInput.value = goal;

                // Update loading state
                if (loading) {
                    loadingIndicator.classList.remove('hidden');
                    generatePathBtn.disabled = true;
                    goalInput.disabled = true;
                    resetAllBtn.disabled = true;
                } else {
                    loadingIndicator.classList.add('hidden');
                    generatePathBtn.disabled = !goal; // Enable only if goal is not empty
                    goalInput.disabled = false;
                    resetAllBtn.disabled = false;
                }

                // Clear messages and errors when new action starts
                if (loading) {
                    messageDisplay.innerHTML = '';
                    errorDisplay.innerHTML = '';
                }

                // Render learning path
                learningPathList.innerHTML = '';
                if (learningPath.length > 0) {
                    learningPathSection.classList.remove('hidden');

                    // Find the last concept in the path (the "search content")
                    const searchConcept = learningPath[learningPath.length - 1];
                    // Check if all prerequisites for the search concept are in userKnownConcepts
                    const prereqs = KNOWLEDGE_GRAPH[searchConcept]?.prerequisites || [];
                    const allPrereqsComplete = prereqs.every(pr => userKnownConcepts.has(pr));

                    // If all prerequisites are complete, show congratulations message
                    if (allPrereqsComplete && learningPath.length > 1) {
                        messageDisplay.innerHTML = `
                            <div class="p-3 bg-blue-100 border border-blue-300 text-blue-800 rounded-lg flex items-center mb-4">
                                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                </svg>
                                Congratulations! All prerequisites for <b>${searchConcept}</b> are complete. You can now access its resources.
                            </div>
                        `;
                    }

                    learningPath.forEach((concept, index) => {
                        const listItem = document.createElement('li');
                        listItem.className = 'bg-white p-5 rounded-lg shadow-md border border-gray-200 hover:shadow-xl transition-shadow duration-300';

                        // For the search concept, gray out links unless all prereqs are complete
                        let resourcesHtml = '';
                        if (KNOWLEDGE_GRAPH[concept]?.resources.length > 0) {
                            resourcesHtml = `<ul class="list-disc list-inside text-gray-600 space-y-1 mt-2">` +
                                KNOWLEDGE_GRAPH[concept].resources.map(res => {
                                    // If this is the search concept and prereqs are NOT complete, gray out
                                    if (concept === searchConcept && !allPrereqsComplete) {
                                        return `<li>
                                            <span class="text-gray-400 cursor-not-allowed" title="Complete all prerequisites to unlock this resource.">
                                                ${res.title} (${res.type})
                                            </span>
                                        </li>`;
                                    } else {
                                        return `<li>
                                            <a href="${res.url}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">
                                                ${res.title} (${res.type})
                                            </a>
                                        </li>`;
                                    }
                                }).join('') +
                                `</ul>`;
                        } else {
                            resourcesHtml = `<p class="text-gray-500 italic mt-2">No specific resources listed for this concept.</p>`;
                        }

                        listItem.innerHTML = `
                            <div class="flex items-center mb-3">
                                <span class="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-purple-500 text-white rounded-full font-bold text-sm mr-4">
                                    ${index + 1}
                                </span>
                                <h3 class="text-xl font-semibold text-purple-700">${concept}</h3>
                            </div>
                            <div class="pl-12">
                                ${resourcesHtml}
                                <div class="mt-4 flex flex-wrap gap-2">
                                    <button data-concept="${concept}" class="complete-btn px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600 transition-colors duration-200 shadow-sm">
                                        Mark as Complete
                                    </button>
                                    <button data-concept="${concept}" class="struggle-btn px-4 py-2 bg-yellow-500 text-white rounded-lg text-sm font-medium hover:bg-yellow-600 transition-colors duration-200 shadow-sm">
                                        Mark as Struggling
                                    </button>
                                </div>
                            </div>
                        `;
                        learningPathList.appendChild(listItem);
                    });

                    // Attach event listeners to new buttons
                    document.querySelectorAll('.complete-btn').forEach(button => {
                        button.onclick = (event) => handleCompleteConcept(event.target.dataset.concept);
                    });
                    document.querySelectorAll('.struggle-btn').forEach(button => {
                        button.onclick = (event) => handleStrugglingConcept(event.target.dataset.concept);
                    });

                } else {
                    learningPathSection.classList.add('hidden');
                }

                // Render known concepts
                knownConceptsList.innerHTML = '';
                if (userKnownConcepts.size > 0) {
                    userKnownConcepts.forEach(concept => {
                        const li = document.createElement('li');
                        li.textContent = concept;
                        knownConceptsList.appendChild(li);
                    });
                } else {
                    knownConceptsList.innerHTML = '<li class="italic text-gray-500">No concepts marked as known yet.</li>';
                }

                // Render struggling concepts
                strugglingConceptsList.innerHTML = '';
                if (userStrugglingConcepts.size > 0) {
                    userStrugglingConcepts.forEach(concept => {
                        const li = document.createElement('li');
                        li.textContent = concept;
                        strugglingConceptsList.appendChild(li);
                    });
                } else {
                    strugglingConceptsList.innerHTML = '<li class="italic text-gray-500">No concepts marked as struggling yet.</li>';
                }
            }

            // --- LLM Interaction Function ---
            async function generateLearningPath() {
                loading = true;
                updateUI();
                errorDisplay.innerHTML = ''; // Clear previous errors
                messageDisplay.innerHTML = ''; // Clear previous messages

                // Data to send to Flask backend
                const requestData = {
                    goal: goal,
                    known_concepts: Array.from(userKnownConcepts),
                    struggling_concepts: Array.from(userStrugglingConcepts)
                };

                try {
                    // Send request to your Flask backend
                    const response = await fetch('http://127.0.0.1:5000/generate_path', { // Flask server URL
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(requestData)
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(`Backend error: ${response.status} - ${errorData.error || JSON.stringify(errorData)}`);
                    }

                    const result = await response.json();
                    console.log("Backend result:", result); // Debug

                    let rawPath = result.path || [];
                    // Remove concepts already marked as known, except the last one (search concept)
                    if (rawPath.length > 1) {
                        rawPath = rawPath.filter((concept, idx) => {
                            // Always keep the last concept (search concept)
                            if (idx === rawPath.length - 1) return true;
                            return !userKnownConcepts.has(concept);
                        });
                    }
                    learningPath = rawPath;
                    userKnownConcepts = new Set(result.known_concepts || []);
                    userStrugglingConcepts = new Set(result.struggling_concepts || []);
                    displayMessage('Learning path generated successfully!');

                } catch (err) {
                    console.error("Error generating learning path:", err);
                    displayError(`Failed to generate path: ${err.message}. Ensure the Python Flask server is running.`);
                } finally {
                    loading = false;
                    updateUI();
                }
            }

            // --- Event Handlers ---
            goalInput.addEventListener('input', (e) => {
                goal = e.target.value;
                updateUI(); // Update button state
            });

            generatePathBtn.addEventListener('click', generateLearningPath);

            resetAllBtn.addEventListener('click', () => {
                goal = '';
                userKnownConcepts = new Set();
                userStrugglingConcepts = new Set();
                learningPath = [];
                displayMessage('Knowledge state reset.');
                updateUI();
                learningPathSection.classList.add('hidden'); // Hide path section on reset
            });

            function handleCompleteConcept(concept) {
                userKnownConcepts.add(concept);
                userStrugglingConcepts.delete(concept); // Remove from struggling if completed
                displayMessage(`"${concept}" marked as complete! Regenerating path...`);
                // Regenerate path after user interaction
                setTimeout(generateLearningPath, 500); // Small delay for message visibility
            }

            function handleStrugglingConcept(concept) {
                userStrugglingConcepts.add(concept);
                displayMessage(`"${concept}" marked as struggling. Regenerating path for review...`);
                // Regenerate path after user interaction
                setTimeout(generateLearningPath, 500); // Small delay for message visibility
            }

            // --- Message Display Helpers ---
            function displayMessage(msg) {
                messageDisplay.innerHTML = `
                    <div class="p-3 bg-green-100 border border-green-300 text-green-800 rounded-lg flex items-center">
                        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                        </svg>
                        ${msg}
                    </div>
                `;
            }

            function displayError(msg) {
                errorDisplay.innerHTML = `
                    <div class="p-3 bg-red-100 border border-red-300 text-red-800 rounded-lg flex items-center">
                        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                        </svg>
                        ${msg}
                    </div>
                `;
            }

            // Initial UI render
            updateUI();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

def build_path_from_knowledge_graph(goal_concept, known_concepts, struggling_concepts, knowledge_graph):
    """
    Recursively builds a path of prerequisites for the goal_concept,
    skipping concepts already in known_concepts.
    Struggling concepts are prioritized to appear earlier if possible.
    """
    path = []
    visited = set()

    def dfs(concept):
        if concept in visited or concept in known_concepts:
            return
        visited.add(concept)
        for prereq in knowledge_graph.get(concept, {}).get("prerequisites", []):
            dfs(prereq)
        path.append(concept)

    # First, add struggling concepts and their prerequisites
    for s_concept in struggling_concepts:
        dfs(s_concept);
    # Then, add the goal concept and its prerequisites
    dfs(goal_concept);

    # Remove duplicates while preserving order
    seen = set();
    ordered_path = [];
    for c in path:
        if c not in seen:
            seen.add(c);
            ordered_path.append(c);
    return ordered_path;

@app.route('/generate_path', methods=['POST'])
def generate_path_endpoint():
    """
    API endpoint to generate the learning path.
    Receives data from the frontend and builds the path using the knowledge graph.
    Uses the dynamic knowledge graph if available, else falls back to the static one.
    """
    data = request.get_json()
    goal = data.get('goal', '')
    known_concepts = set(data.get('known_concepts', []))
    struggling_concepts = set(data.get('struggling_concepts', []))

    #Use dynamic KG if available, else fallback to static
    knowledge_graph = DYNAMIC_KNOWLEDGE_GRAPH if DYNAMIC_KNOWLEDGE_GRAPH else KNOWLEDGE_GRAPH

    # Try to match the goal to a concept in the knowledge graph
    matched_goal = None
    goal_lower = goal.strip().lower()
    for concept in knowledge_graph:
        if goal_lower in concept.lower():
            matched_goal = concept
            break
    if not matched_goal:
        # fallback: use the first concept
        matched_goal = list(knowledge_graph.keys())[0]

    # Build the path using the recursive function
    path = build_path_from_knowledge_graph(
        matched_goal,
        known_concepts,
        struggling_concepts,
        knowledge_graph
    )

    print(f"Generated path (recursive): {path}")
    return jsonify({
        "path": path,
        "known_concepts": list(known_concepts),
        "struggling_concepts": list(struggling_concepts)
    });


if __name__ == '__main__':
    # To run this Flask app:
    # 1. Save this code as app.py (or any other .py file)
    # 2. Make sure you have Flask and requests installed: pip install Flask Flask-Cors requests
    # 3. Run from your terminal: python app.py
    #    or: flask run
    # The app will typically run on http://127.0.0.1:5000/
    app.run(debug=True) # debug=True enables auto-reloading and better error messages



