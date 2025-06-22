# AI-Powered Support Ticket Routing & Processing - Case Study

This project demonstrates an AI-powered system for automatically routing and processing customer support tickets. It uses Google's **gemini-1.5-flash** Large Language Model (LLM) via the `pydantic-ai` library to categorize tickets, assess urgency, generate summaries, and then route them to specialized "solver" agents. These solvers provide structured outputs like bug reports, draft responses, or security alerts, including assigning a responsible team.

## Features

-   **Automated Ticket Categorization:** Classifies tickets into predefined categories (Bugs, Query, Request, Security, Correctness, Miscellaneous).
-   **Urgency Assessment:** Determines ticket urgency (High, Medium, Low).
-   **Concise Summarization:** Generates a one-sentence summary of the ticket.
-   **Specialized Solvers:** Routes tickets to different AI agents tailored to handle specific categories.
-   **Structured Output:** Solvers produce Pydantic models (e.g., `BugReport`, `DraftResponse`) ensuring consistent and usable data.
-   **Team Assignment:** Solver agents determine and assign the most appropriate internal team (e.g., Frontend, Backend, Security).
-   **Error Handling:** Includes mechanisms for handling LLM rate limits and malformed responses.
-   **Modular Design:** Separates routing, orchestration, and solving logic into distinct agent modules.

## How It Works

The system processes tickets through a three-stage pipeline:

1.  **Router (`agents/router.py`):**
    *   A raw ticket (containing subject, message, customer metadata) is received.
    *   The `_ROUTER_AGENT` (powered by `gemini-1.5-flash`) analyzes the ticket content based on a detailed system prompt and Pydantic schema definitions.
    *   It outputs a `RoutingSlip` Pydantic model containing the determined `category`, `urgency`, and a `summary` of the ticket.

2.  **Orchestrator (`agents/orchestrator.py`):**
    *   This component receives the original ticket and the `RoutingSlip` from the Router.
    *   Using a `_HANDLER_MAP`, it identifies the appropriate solver function based on the `RoutingSlip.category`.
    *   It then invokes the selected solver, passing along the ticket data and the summary.

3.  **Solvers (`agents/solvers.py`):**
    *   Each category (Bug, Query, etc.) has a dedicated solver function (e.g., `generate_bug_report`, `generate_draft_response`).
    *   Each solver function utilizes its own specialized `_SOLVER_AGENT` (also `gemini-1.5-flash`), configured with a specific system prompt and output Pydantic model (e.g., `BugReport`, `DraftResponse`, `SecurityAlert`).
    *   The solver agent processes the ticket information and summary to generate its structured output.
    *   Crucially, within the prompt and Pydantic schema for each solver's output, instructions are given to the LLM to determine and include the most appropriate `assigned_team` (e.g., Backend, Frontend, Security, Customer Support).

The final output is a JSON object containing the original ticket ID, the routing slip details, and the structured data from the relevant solver, including the assigned team.

## Flow Diagram

The following diagram illustrates the high-level flow of a ticket through the system:

<div align="center">
![Flow Chart](https://github.com/mukund399/supportticket/blob/main/assets/flow_chart.png)
</dvi>

## LLM & Technology Stack

-   **LLM:** Google `gemini-1.5-flash` (accessed via Vertex AI, indicated by `google-gla` prefix).
-   **Orchestration Library:** `pydantic-ai` for streamlined interaction with LLMs and ensuring structured, Pydantic-validated outputs.
-   **Data Validation:** `Pydantic` for defining data schemas and validation.
-   **Environment Management:** `python-dotenv` for managing API keys and configurations.
-   **Core Python Libraries:** `enum`, `json`.

## Evaluation Results

The system was evaluated on a sample set of 12 diverse support tickets. The key performance indicators are as follows:

**Overall Performance:**
*   **Total Tickets Processed:** 12
*   **Average Processing Time:** 2.38 seconds per ticket

**Router Agent Evaluation:**
*   **Routing Accuracy (Category):** 91.67% (11 out of 12 tickets correctly categorized)
*   **Urgency Accuracy:** 91.67% (11 out of 12 tickets assigned correct urgency)

**Solver Agents Evaluation:**
*   **Solver Success Rate:** 100.00% (All 12 tickets successfully processed by a solver agent without critical errors)
*   **Team Assignment Accuracy:** 83.33% (10 out of 12 tickets assigned to the most appropriate team by the solver)

These initial results are promising, demonstrating high accuracy in routing and a good understanding of team assignment by the AI agents. The slight discrepancies in team assignment indicate areas for further prompt refinement or more contextual information for the solver agents.

## Future Work & Improvements

This PoC lays the groundwork for a more sophisticated AI-powered support system. Potential future enhancements include:

1.  **Granular Sub-Team Assignment:**
    *   Enhance solver prompts and `AssignedTeam` enums to include sub-teams (e.g., `Backend-API`, `Backend-Database`, `Frontend-Mobile`, `UI/UX-Web`). This would require more nuanced analysis by the solver LLM based on deeper technical details in the ticket.

2.  **Integration with Ticketing Platforms (e.g., JIRA, Zendesk):**
    *   Develop connectors to automatically create new tickets in platforms like JIRA using the structured output from the AI (e.g., `BugReport.title` becomes JIRA issue summary, `reproduction_steps` populate the description).
    *   Enable two-way sync: Update JIRA ticket status based on internal actions, or pull JIRA comments back into the AI's context for follow-up.

3.  **RAG Application for Automated Customer Support:**
    *   Build a Retrieval Augmented Generation (RAG) system where the "Query Solver" can access a knowledge base (FAQs, product documentation, past resolved tickets).
    *   When a "QUERY" ticket comes in, the RAG system would retrieve relevant information and use an LLM (like `gemini-1.5-flash`) to generate a comprehensive, context-aware draft response, potentially resolving many queries automatically without human intervention.

4.  **AI-Powered Fix Suggestions (Coder LLM / Cursor Integration):**
    *   For tickets categorized as "BUGS," after the `BugReport` is generated, invoke a specialized Coder LLM (e.g., a fine-tuned Gemini model for code, or integrate with tools like Cursor).
    *   This Coder LLM could analyze the bug description and potentially relevant code snippets (if available or retrievable) to suggest potential code fixes, patches, or debugging steps for engineers.

5.  **Enhanced Evaluation Framework (`evaluation/`):**
    *   Implement more robust metrics, including semantic similarity for summaries, F1 scores for multi-class classification (category, team), and human-in-the-loop validation for generated content quality.
    *   Create a standardized test dataset for consistent benchmarking.

6.  **Continuous Feedback Loop & Fine-Tuning:**
    *   Implement a mechanism for human agents to correct AI outputs (category, urgency, summary, team, solver-generated content).
    *   Use this feedback data to periodically fine-tune the LLM prompts or the models themselves for improved accuracy and relevance.

7.  **Asynchronous Processing & Scalability:**
    *   Refactor `main.py` to use asynchronous operations (e.g., `asyncio`, `aiohttp`) for making LLM calls, improving throughput for batch processing.
    *   Explore message queues (e.g., RabbitMQ, Kafka) for a more robust and scalable ticket ingestion pipeline.

## Project Structure


your-name-case-study/
├── main.py # Main script to run a batch of sample tickets
├── agents/ # Core AI logic
│ ├── init.py
│ ├── router.py # Handles initial ticket analysis and routing slip generation
│ ├── orchestrator.py # Routes tickets to appropriate solvers based on category
│ └── solvers.py # Contains specialized AI agents for different ticket types
├── evaluation/ # For scripts/notebooks evaluating model performance
├── docs/ # For detailed documentation, diagrams
├── .env.example # Example environment file for API keys
├── requirements.txt # Python dependencies
├── ai_chat_history.txt # Full AI conversation history for this project
└── README.md # This file

Generated code
## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd your-name-case-study
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Copy `.env.example` to a new file named `.env`:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file and add your Google Cloud credentials or API key. For `google-gla:gemini-1.5-flash`, this typically involves:
    *   Ensuring you have Application Default Credentials (ADC) set up by running `gcloud auth application-default login`.
    *   Your `gcloud` CLI should be configured for the correct Google Cloud Project that has Vertex AI enabled.
    *   You might need to set `GCP_PROJECT="your-gcp-project-id"` and `GCP_REGION="your-gcp-region"` (e.g., `us-central1`) in your `.env` file if `pydantic-ai` or the underlying Google libraries require them explicitly.

## Running the Code

Execute the `main.py` script to process the sample tickets defined within it:

```bash
python main.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

The script will print detailed output for each ticket, including the routing slip and the solver's structured response.

License

(Consider adding a license, e.g., MIT License. If so, add a LICENSE file and uncomment the line below)

<!-- This project is licensed under the MIT License - see the LICENSE file for details. -->

Generated code
This README is now much more comprehensive and should serve well for your case study! Remember to replace `<your-repo-url>` with the actual URL once you host it on GitHub.
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
