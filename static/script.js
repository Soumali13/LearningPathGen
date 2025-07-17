// KNOWLEDGE_GRAPH will now be dynamically loaded from the backend
let KNOWLEDGE_GRAPH = {}; // Initialize as empty

// State variables
let kgTopic = '';
let isKgLoading = false;
let kgMessage = '';
let kgError = '';

let goal = '';
let userKnownConcepts = new Set();
let userStrugglingConcepts = new Set();
let learningPath = [];
let isPathLoading = false; // Renamed from 'loading' for clarity

// DOM Elements
const kgTopicInput = document.getElementById('kgTopicInput');
const generateKgBtn = document.getElementById('generateKgBtn');
const kgLoadingIndicator = document.getElementById('kgLoadingIndicator');
const kgMessageDisplay = document.getElementById('kgMessageDisplay');
const kgErrorDisplay = document.getElementById('kgErrorDisplay');

const goalInput = document.getElementById('goalInput');
const generatePathBtn = document.getElementById('generatePathBtn');
const messageDisplay = document.getElementById('messageDisplay');
const errorDisplay = document.getElementById('errorDisplay');
const loadingIndicator = document.getElementById('loadingIndicator'); // For path generation
const learningPathSection = document.getElementById('learningPathSection');
const learningPathList = document.getElementById('learningPathList');
const knownConceptsList = document.getElementById('knownConceptsList');
const strugglingConceptsList = document.getElementById('strugglingConceptsList');
const resetAllBtn = document.getElementById('resetAllBtn');

// --- UI Update Functions ---
function updateUI() {
    // KG Section UI
    kgTopicInput.value = kgTopic;
    kgLoadingIndicator.classList.toggle('hidden', !isKgLoading);
    generateKgBtn.disabled = isKgLoading || !kgTopic;
    kgTopicInput.disabled = isKgLoading;

    kgMessageDisplay.textContent = kgMessage;
    kgErrorDisplay.textContent = kgError;

    // Path Generation Section UI
    goalInput.value = goal;
    loadingIndicator.classList.toggle('hidden', !isPathLoading);
    generatePathBtn.disabled = isPathLoading || !goal || Object.keys(KNOWLEDGE_GRAPH).length === 0; // Disable if no KG
    goalInput.disabled = isPathLoading || Object.keys(KNOWLEDGE_GRAPH).length === 0;
    resetAllBtn.disabled = isKgLoading || isPathLoading; // Disable reset if either is loading

    // Clear messages and errors when new action starts
    if (isPathLoading) {
        messageDisplay.innerHTML = '';
        errorDisplay.innerHTML = '';
    }

    // Render learning path
    learningPathList.innerHTML = '';
    if (learningPath.length > 0) {
        learningPathSection.classList.remove('hidden');
        learningPath.forEach((concept, index) => {
            const listItem = document.createElement('li');
            listItem.className = 'bg-white p-5 rounded-lg shadow-md border border-gray-200 hover:shadow-xl transition-shadow duration-300';

            // Ensure concept exists in KNOWLEDGE_GRAPH before accessing its properties
            const resources = KNOWLEDGE_GRAPH[concept] && KNOWLEDGE_GRAPH[concept].resources ? KNOWLEDGE_GRAPH[concept].resources : [];
            const resourcesHtml = resources.length > 0
                ? `<ul class="list-disc list-inside text-gray-600 space-y-1 mt-2">
                    ${resources.map(res => `
                        <li>
                            <a href="${res.url}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">
                                ${res.title} (${res.type})
                            </a>
                        </li>
                    `).join('')}
                   </ul>`
                : `<p class="text-gray-500 italic mt-2">No specific resources listed for this concept.</p>`;

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

// --- Knowledge Graph Generation Function ---
async function generateKnowledgeGraph() {
    isKgLoading = true;
    kgMessage = '';
    kgError = '';
    updateUI();

    const topic = kgTopicInput.value.trim();
    if (!topic) {
        kgError = 'Please enter a topic for the Knowledge Graph.';
        isKgLoading = false;
        updateUI();
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:5000/generate_knowledge_graph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Backend error: ${response.status} - ${errorData.error || JSON.stringify(errorData)}`);
        }

        const result = await response.json();
        if (result.knowledge_graph && Object.keys(result.knowledge_graph).length > 0) {
            KNOWLEDGE_GRAPH = result.knowledge_graph;
            kgMessage = `Knowledge Graph for "${topic}" generated successfully!`;
            console.log('Generated KNOWLEDGE_GRAPH:', KNOWLEDGE_GRAPH);

            // Render the knowledge graph visualization
            renderKnowledgeGraph(KNOWLEDGE_GRAPH);
        } else {
            kgError = 'Failed to generate a valid Knowledge Graph. Please try a different topic.';
            console.error('Empty or invalid KG from backend:', result);
        }
    } catch (err) {
        console.error('Error generating Knowledge Graph:', err);
        kgError = `Failed to generate KG: ${err.message}. Ensure Flask server is running.`;
    } finally {
        isKgLoading = false;
        updateUI();
    }
}

// --- Learning Path Generation Function ---
async function generateLearningPath() {
    if (Object.keys(KNOWLEDGE_GRAPH).length === 0) {
        displayError('Please generate a Knowledge Graph first.');
        return;
    }

    isPathLoading = true;
    updateUI();
    errorDisplay.innerHTML = ''; // Clear previous errors
    messageDisplay.innerHTML = ''; // Clear previous messages

    const requestData = {
        goal: goal,
        known_concepts: Array.from(userKnownConcepts),
        struggling_concepts: Array.from(userStrugglingConcepts),
        knowledge_graph: KNOWLEDGE_GRAPH // Pass the dynamic KG to the backend
    };

    try {
        const response = await fetch('http://127.0.0.1:5000/generate_path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Backend error: ${response.status} - ${errorData.error || JSON.stringify(errorData)}`);
        }

        const result = await response.json();
        learningPath = result.path || [];
        displayMessage('Learning path generated successfully!');

    } catch (err) {
        console.error("Error generating learning path:", err);
        displayError(`Failed to generate path: ${err.message}. Ensure the Python Flask server is running.`);
    } finally {
        isPathLoading = false;
        updateUI();
    }
}

// --- Event Handlers ---
kgTopicInput.addEventListener('input', (e) => {
    kgTopic = e.target.value;
    updateUI();
});

generateKgBtn.addEventListener('click', generateKnowledgeGraph);

goalInput.addEventListener('input', (e) => {
    goal = e.target.value;
    updateUI();
});

generatePathBtn.addEventListener('click', generateLearningPath);

resetAllBtn.addEventListener('click', () => {
    kgTopic = '';
    KNOWLEDGE_GRAPH = {}; // Reset KG
    isKgLoading = false;
    kgMessage = '';
    kgError = '';

    goal = '';
    userKnownConcepts = new Set();
    userStrugglingConcepts = new Set();
    learningPath = [];
    isPathLoading = false;
    displayMessage('Knowledge state reset.');
    updateUI();
    learningPathSection.classList.add('hidden'); // Hide path section on reset
});

function handleCompleteConcept(concept) {
    userKnownConcepts.add(concept);
    userStrugglingConcepts.delete(concept);
    displayMessage(`"${concept}" marked as complete! Regenerating path...`);
    setTimeout(generateLearningPath, 500);
}

function handleStrugglingConcept(concept) {
    userStrugglingConcepts.add(concept);
    displayMessage(`"${concept}" marked as struggling. Regenerating path for review...`);
    setTimeout(generateLearningPath, 500);
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

function renderKnowledgeGraph(knowledgeGraph) {
    const container = document.getElementById('knowledgeGraphContainer');
    container.innerHTML = ''; // Clear previous graph

    // Create a container for the nodes
    const nodesContainer = document.createElement('div');
    nodesContainer.className = 'flex flex-wrap gap-4';

    Object.keys(knowledgeGraph).forEach((concept) => {
        const conceptData = knowledgeGraph[concept];
        const prerequisites = conceptData.prerequisites || [];

        // Create a node for the concept
        const node = document.createElement('div');
        node.className = 'bg-purple-100 p-4 rounded-lg shadow-md border border-purple-300 text-center w-48';

        // Add concept name
        const conceptTitle = document.createElement('h3');
        conceptTitle.className = 'text-base font-semibold text-purple-700';
        conceptTitle.textContent = concept;
        node.appendChild(conceptTitle);

        // Add prerequisites
        const prerequisitesTitle = document.createElement('p');
        prerequisitesTitle.className = 'text-sm font-medium text-gray-600 mt-2';
        prerequisitesTitle.textContent = 'Prerequisites:';
        node.appendChild(prerequisitesTitle);

        const prerequisitesList = document.createElement('ul');
        prerequisitesList.className = 'list-disc list-inside text-gray-500';
        prerequisites.forEach((prerequisite) => {
            const prerequisiteItem = document.createElement('li');
            prerequisiteItem.className = 'text-sm'; 
            prerequisiteItem.textContent = prerequisite;
            prerequisitesList.appendChild(prerequisiteItem);
        });
        node.appendChild(prerequisitesList);

        // Append the node to the container
        nodesContainer.appendChild(node);
    });

    // Append the nodes container to the main container
    container.appendChild(nodesContainer);
}

// Initial UI render
updateUI();