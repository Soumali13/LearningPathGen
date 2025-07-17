import json
import requests
import re
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS # Required for cross-origin requests from frontend

app = Flask(__name__)
CORS(app) # Enable CORS for frontend requests

# Cache for storing knowledge graphs by topic
knowledge_graph_cache = {}

# KNOWLEDGE_GRAPH will now be dynamically generated.
# We keep a placeholder or a default structure for reference if needed,
# but the primary source will be the LLM.
# For simplicity, resources are still hardcoded in the frontend's KNOWLEDGE_GRAPH
# as generating dynamic URLs for resources from LLM is out of scope for this example.
# In a real app, resources would be looked up from a separate database.
DEFAULT_KNOWLEDGE_GRAPH = {
    "Introduction to ML": {
        "prerequisites": [],
        "resources": [
            {"type": "video", "title": "ML Basics Explained", "url": "https://www.youtube.com/watch?v=GwIo3gDZCVQ"},
            {"type": "article", "title": "What is Machine Learning?", "url": "https://www.ibm.com/cloud/learn/machine-learning"}
        ]
    },
    "Supervised Learning": {
        "prerequisites": ["Introduction to ML"],
        "resources": [
            {"type": "video", "title": "Supervised Learning Concepts", "url": "https://www.youtube.com/watch?v=Gv9_4yMHFhI"},
            {"type": "article", "title": "Linear Regression Tutorial", "url": "https://www.geeksforgeeks.org/linear-regression-in-machine-learning/"}
        ]
    },
    "Unsupervised Learning": {
        "prerequisites": ["Introduction to ML"],
        "resources": [
            {"type": "video", "title": "Unsupervised Learning Intro", "url": "https://www.youtube.com/watch?v=3tNSlKgs3dc"},
            {"type": "article", "title": "Clustering Algorithms", "url": "https://towardsdatascience.com/clustering-algorithms-101-50d3c8d60a02"}
        ]
    },
    "Deep Learning Basics": {
        "prerequisites": ["Supervised Learning", "Unsupervised Learning"],
        "resources": [
            {"type": "video", "title": "Neural Networks Explained", "url": "https://www.youtube.com/watch?v=aircAruvnKk"},
            {"type": "article", "title": "Intro to Deep Learning", "url": "https://www.ibm.com/cloud/learn/deep-learning"}
        ]
    },
    "Natural Language Processing (NLP)": {
        "prerequisites": ["Deep Learning Basics"],
        "resources": [
            {"type": "video", "title": "NLP Fundamentals", "url": "https://www.youtube.com/watch?v=8uYjQ5x6cRw"},
            {"type": "article", "title": "Transformers in NLP", "url": "https://huggingface.co/transformers/"
            }
        ]
    },
    "Computer Vision (CV)": {
        "prerequisites": ["Deep Learning Basics"],
        "resources": [
            {"type": "video", "title": "CV Intro and Applications", "url": "https://www.youtube.com/watch?v=YRhxdVk_sIs"},
            {"type": "article", "title": "Convolutional Neural Networks", "url": "https://towardsdatascience.com/a-guide-to-convolutional-neural-networks-cnns-4bdc471f5de4"}
        ]
    },
    "Reinforcement Learning": {
        "prerequisites": ["Introduction to ML"],
        "resources": [
            {"type": "video", "title": "RL Basics", "url": "https://www.youtube.com/watch?v=JgvyzIkgxF0"},
            {"type": "article", "title": "Q-Learning Explained", "url": "https://www.geeksforgeeks.org/q-learning-in-reinforcement-learning/"}
        ]
    },
    "MLOps Fundamentals": {
        "prerequisites": ["Introduction to ML"],
        "resources": [
            {"type": "video", "title": "What is MLOps?", "url": "https://www.youtube.com/watch?v=06-AZXmwHjo"},
            {"type": "article", "title": "MLOps Best Practices", "url": "https://neptune.ai/blog/mlops-practices"}
        ]
    }
}



def call_gemini_api(prompt_text: str, response_schema: dict) -> dict:
    """
    Calls the Gemini AI model with the given prompt and a specific response schema.
    """
    chat_history = [{"role": "user", "parts": [{"text": prompt_text}]}]

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    api_key = "AIzaSyDoCNYecUmxS4FkwRvr7ESnQWL7Ju8QxI0" # This will be automatically populated by Canvas runtime
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
        response.raise_for_status()
        result = response.json()

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
            return {}
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}. Raw response: {json_string if 'json_string' in locals() else raw_llm_response}")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred during API call: {e}")
        return {}

@app.route('/')
def index():
    """Serves the main HTML page."""
    return app.send_static_file('index.html')

@app.route('/generate_knowledge_graph', methods=['POST'])
def generate_knowledge_graph_endpoint():
    """
    API endpoint to dynamically generate a knowledge graph based on a topic.
    Caches the knowledge graph for subsequent requests.
    """
    data = request.get_json()
    topic = data.get('topic', '').strip().lower()

    if not topic:
        return jsonify({"error": "Topic is required to generate knowledge graph."}), 400

    # Check if the knowledge graph for the topic is already cached
    if topic in knowledge_graph_cache:
        print(f"Returning cached knowledge graph for topic: '{topic}'")
        return jsonify({"knowledge_graph": knowledge_graph_cache[topic]})

    print(f"Generating knowledge graph for topic: '{topic}'")

    kg_prompt = f"""
        You are an AI assistant specialized in generating structured knowledge graphs for educational purposes.
        Given a topic, generate a knowledge graph as a JSON object.
        The keys of the JSON object MUST be the concept names (e.g., "Introduction to ML").
        Each value associated with a concept key MUST be an object containing:
        - "prerequisites": An array of concept names that must be learned before this concept.
        - "resources": An array of objects, each with:
            - "type" (e.g., "video", "article", "book"),
            - "title" (e.g., "Intro to X"),
            - "url" (e.g., "https://example.com/resource").
        Ensure each concept has:
        - At least 3 articles (with accurate URLs),
        - At least 2 video links (with accurate URLs),
        - At least 1 book (with accurate title and URL).
        Provide real, valid URLs for resources where possible. If a real URL is not available, use "https://example.com/placeholder_resource".

        Ensure the concepts are relevant to the topic and have logical prerequisites.
        Aim for 8-12 core concepts for the given topic.

        **Topic:** {topic}
    """

    kg_schema = {
        "type": "OBJECT",
        "patternProperties": {
            ".*": {  # Allows any concept name as a key
                "type": "OBJECT",
                "properties": {
                    "prerequisites": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "resources": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "type": {"type": "STRING"},
                                "title": {"type": "STRING"},
                                "url": {"type": "STRING", "nullable": True}  # URL can be null
                            },
                            "required": ["type", "title"]
                        }
                    }
                },
                "required": ["prerequisites", "resources"]
            }
        },
        "additionalProperties": False
    }

    generated_kg = call_gemini_api(kg_prompt, kg_schema)

    if generated_kg:
        print(f"Type of generated_kg from LLM: {type(generated_kg)}")
        final_kg_structure = {}

        if isinstance(generated_kg, dict):
            # If LLM returns a dict, use it directly
            final_kg_structure = generated_kg
        elif isinstance(generated_kg, list):
            # If LLM returns a list, try to convert it to the expected dict format
            # This handles cases like [{"concept_name": "X", ...}, {"concept_name": "Y", ...}]
            for item in generated_kg:
                if isinstance(item, dict) and "concept_name" in item: # Assuming 'concept_name' might be the key if it's a list of objects
                    concept_name = item.pop("concept_name") # Remove and use as key
                    final_kg_structure[concept_name] = item
                elif isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] not in ["prerequisites", "resources"]:
                    # Handle cases where LLM might return a list of single-key dicts like [{"Concept A": {...}}, {"Concept B": {...}}]
                    concept_name = list(item.keys())[0]
                    final_kg_structure[concept_name] = item[concept_name]
                else:
                    print(f"Warning: Skipping unexpected item structure in generated KG list: {item}")
        else:
            print("Error: Generated knowledge graph has an unexpected top-level structure (not dict or list).")
            return jsonify({"error": "Generated knowledge graph has an unexpected top-level structure."}), 500

        # Ensure all resources have a URL, even if placeholder
        for concept_data in final_kg_structure.values():
            for resource in concept_data.get('resources', []):
                if 'url' not in resource or not resource['url']:
                    resource['url'] = "https://example.com/placeholder_resource";

        # Cache the generated knowledge graph
        knowledge_graph_cache[topic] = final_kg_structure
        print(f"Generated and cached knowledge graph for topic: '{topic}'")
        print(f"Final KG structure sent to frontend: {final_kg_structure}")
        return jsonify({"knowledge_graph": final_kg_structure})
    else:
        print("Error: LLM failed to generate knowledge graph.")
        return jsonify({"error": "Failed to generate knowledge graph from AI model."}), 500


@app.route('/generate_path', methods=['POST'])
def generate_path_endpoint():
    """
    API endpoint to generate the learning path.
    Receives data from the frontend and calls the Gemini API.
    Now accepts the knowledge_graph from the frontend.
    """
    data = request.get_json()
    goal = data.get('goal', '')
    known_concepts = set(data.get('known_concepts', []))
    struggling_concepts = set(data.get('struggling_concepts', []))
    # Get the dynamically generated knowledge graph from the request body
    dynamic_knowledge_graph = data.get('knowledge_graph', DEFAULT_KNOWLEDGE_GRAPH)

    print(f"Received request for path: Goal='{goal}', Known={known_concepts}, Struggling={struggling_concepts}")
    print(f"Using dynamic knowledge graph for path generation (first 3 concepts): {list(dynamic_knowledge_graph.keys())[:3]}...")

    # Pass the dynamic knowledge graph to the prompt builder
    prompt_text = build_gemini_prompt(goal, known_concepts, struggling_concepts, dynamic_knowledge_graph)
    print(f"\n--- Prompt sent to Gemini API for Path ---\n{prompt_text}\n----------------------------------")

    # The response schema for path generation remains the same
    path_schema = {
        "type": "OBJECT",
        "properties": {
            "path": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            }
        },
        "required": ["path"]
    }

    path_result = call_gemini_api(prompt_text, path_schema)

    if path_result:
        # Filter out known concepts before sending to UI
        # Ensure path_result.get('path', []) is a list before filtering
        generated_path_list = path_result.get('path', [])
        if not isinstance(generated_path_list, list):
            print(f"Warning: LLM returned non-list for path: {generated_path_list}. Attempting to convert.")
            # Try to convert to list if it's a single string or other unexpected type
            if isinstance(generated_path_list, str):
                try:
                    generated_path_list = json.loads(generated_path_list)  # Might be a JSON string of a list
                except json.JSONDecodeError:
                    generated_path_list = [generated_path_list]  # Treat as single concept
            else:
                generated_path_list = []  # Fallback to empty list
        filtered_path = [concept for concept in generated_path_list if concept in dynamic_knowledge_graph and concept not in known_concepts]
        print("Filtered path:", filtered_path)
        return jsonify({"path": filtered_path})
    else:
        print("Error: call_gemini_api returned empty result for path generation.")
        return jsonify({"error": "Failed to generate learning path from AI model."}), 500

def build_gemini_prompt(goal: str, user_known_concepts: set, user_struggling_concepts: set, current_knowledge_graph: dict) -> str:
    """
    Helper function to build the prompt text for the Gemini API.
    Now accepts the current_knowledge_graph as an argument.
    """
    print(f"Type of current_knowledge_graph in build_gemini_prompt: {type(current_knowledge_graph)}")
    # print(f"Current Knowledge Graph in build_gemini_prompt: {current_knowledge_graph}") # Keep this for detailed debugging if needed

    # Ensure current_knowledge_graph is a dictionary as expected
    if not isinstance(current_knowledge_graph, dict):
        print("Error: current_knowledge_graph is not a dictionary in build_gemini_prompt. Using empty KG string.")
        knowledge_graph_str = "Error: Invalid Knowledge Graph structure provided."
    else:
        knowledge_graph_str = "\n".join([
            f"- {concept}: Prerequisites: [{', '.join(data.get('prerequisites', []))}]"
            for concept, data in current_knowledge_graph.items()
        ])

    prompt = f"""
        You are an AI assistant specialized in creating personalized learning paths for Learning Experience.
        Based on the user's goal, their current knowledge, and a provided knowledge graph, generate a sequential learning path.

        **User's Goal:** {goal if goal else 'Understand Machine Learning Concepts'}
        **User's Known Concepts:** {', '.join(user_known_concepts) if user_known_concepts else 'None'}
        **User's Struggling Concepts (prioritize review/re-explanation):** {', '.join(user_struggling_concepts) if user_struggling_concepts else 'None'}

        **Available Concepts and their Prerequisites (Knowledge Graph):**
        {knowledge_graph_str}

        **Instructions:**
        1. Generate a learning path as a JSON array of concept names.
        2. Ensure all prerequisites for a concept are listed before the concept itself in the path.
        3. Prioritize concepts the user is struggling with by placing them earlier or suggesting a review. If a struggling concept's prerequisites are not met, suggest the prerequisites first.
        4. Avoid including concepts the user already knows, unless they are prerequisites for a new, unknown concept.
        5. The path should be logical and progressive towards the user's goal.
        6. If the goal is too broad or already mostly known, suggest next steps or more advanced topics.
        7. Only include concepts from the provided KNOWLEDGE_GRAPH.
        8. The output MUST be a JSON object with a single key "path" which is an array of strings (concept names).

        **Example JSON Output:**
        {{"path": ["Introduction to ML", "Supervised Learning", "Deep Learning Basics"]}}
    """
    return prompt

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    API endpoint to handle chat interactions with Gemini.
    """
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({"error": "Question is required."}), 400

    print(f"Received chat question: {question}")

    chat_prompt = f"""
        You are an AI assistant named Gemini. Answer the user's question based on your knowledge graph and expertise.
        Provide concise and accurate answers. If the question is unclear, ask for clarification.

        **User's Question:** {question}
    """

    chat_schema = {
        "type": "OBJECT",
        "properties": {
            "answer": {"type": "STRING"}
        },
        "required": ["answer"]
    }

    chat_result = call_gemini_api(chat_prompt, chat_schema)

    if chat_result and 'answer' in chat_result:
        return jsonify({"answer": chat_result['answer']})
    else:
        print("Error: call_gemini_api returned empty result for chat.")
        return jsonify({"error": "Failed to get a response from Gemini."}), 500

if __name__ == '__main__':
    app.run(debug=True)
