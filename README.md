# Learning Path Generator

## Overview
`learning_path_advanced.py` is a Flask-based web application that dynamically generates personalized learning paths and visualizes knowledge graphs for educational topics. It leverages the Gemini AI model to create structured knowledge graphs and learning paths based on user input.

## Features
- **Knowledge Graph Generation**: Dynamically generates a knowledge graph for a given topic, including prerequisites and resources (videos, articles, books).
- **Learning Path Generation**: Creates a sequential learning path based on user goals, known concepts, and struggling concepts.
- **Knowledge Graph Visualization**: Displays concepts as nodes with prerequisites and resources.
- **Interactive UI**: Allows users to mark concepts as "complete" or "struggling" and regenerate learning paths accordingly.
- **Caching**: Caches generated knowledge graphs for faster retrieval.

## Requirements
- Python 3.7 or higher
- Flask
- Flask-CORS
- Requests

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/learning-path-generator.git
   cd learning-path-generator
   ```
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python learning_path_advanced.py
   ```
4. Access the web interface at `http://127.0.0.1:5000`.

## Usage
1. Enter your desired learning topic and goals.
2. Specify any known concepts and concepts you are struggling with.
3. View the generated knowledge graph and learning path.
4. Interact with the graph by marking concepts as complete or struggling.
5. Regenerate the learning path as needed.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## API Endpoints

```bash
/generate_knowledge_graph (POST)
```
Description: Generates a knowledge graph for a given topic.
```bash
Response:
{
  "topic": "Machine Learning"
}
{
  "knowledge_graph": {
    "Introduction to ML": {
      "prerequisites": [],
      "resources": [
      ]
    }
  }
}
```
```bash
/generate_path (POST)
```
Description: Generates a learning path based on user input and the knowledge graph.
```bash
Request Body:
{
  "goal": "Understand Deep Learning",
  "known_concepts": ["Introduction to ML"],
  "struggling_concepts": ["Supervised Learning"],
  "knowledge_graph": { ... }
}
{
  "path": ["Supervised Learning", "Deep Learning Basics"]
}
```
## File Structure
- learning_path_advanced.py: Main application file.
- requirements.txt: Dependencies for the project.
- README.md: Documentation for the project.

## Technologies Used
- Backend: Flask
- Frontend: HTML, Tailwind CSS, JavaScript
- AI Integration: Gemini AI model for knowledge graph and learning path generation.

## Known Issues
- Placeholder URLs are used when valid URLs are unavailable.
- The application relies on the Gemini AI model, which requires a valid API key.

## Contact
For questions or feedback, contact soumali.cybernetics@gmail.com. 

## Screenshot
<img width="1890" height="760" alt="Screenshot (3)" src="https://github.com/user-attachments/assets/34485db0-ee6b-4e51-97ec-5d08db56cf38" />

