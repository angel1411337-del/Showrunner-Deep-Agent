Showrunner Command Center - Implementation Walkthrough
We have successfully built the Command and Ops Center UI for the Showrunner agent. This modern "Glassmorphism" interface allows you to visualize the agent's internal state, obligations, and knowledge base.

1. Architecture
The system uses a decoupled architecture to ensure separation of concerns:

Frontend (web/): A React + Vite application using Tailwind CSS v4 for styling. It features a custom dark-mode glassmorphism theme and uses framer-motion for smooth transitions.
Backend (src/showrunner/server/): A FastAPI service that reads the raw JSON artifacts (obligations.json, entities.json) from the latest 
out/
 directory and exposes them via a REST API.
2. Key Features Implemented
Dashboard
Displays high-level metrics: Total Obligations, Open Threads, Key Entities, and High Confidence Events.
Live data fetching from the backend.
Dossier & Obligations
Dossier View: Filters for unresolved plot threads and mysteries.
Obligations Explorer: Shows all items, including resolved ones.
Visuals: Color-coded badges for categories (Plot Thread, Chekhov's Gun, etc.) and confidence scores.
Entity Explorer
Grid view of all entities (Characters, Places, Artifacts) found in the corpus.
Shows mention counts and "Key Entity" status.
3. Technical Fixes & Notes
Tailwind CSS v4
We encountered a build error with PostCSS and Tailwind v4. This was resolved by installing the @tailwindcss/postcss adapter and updating 
postcss.config.js
.

Browser Tool & Environment
We identified an issue where the Antigravity browser tool failed to launch because the Windows environment lacked a $HOME variable.

Fix Applied: We ran [System.Environment]::SetEnvironmentVariable("HOME", $env:USERPROFILE, "User").
Action Required: A full restart of the Antigravity application/IDE is required for this fix to enable the browser tool for future sessions.
4. How to Run
Start Backend:
cd src
uv run uvicorn showrunner.server.main:app --reload --port 8000
Start Frontend:
cd web
npm run dev
Access UI: Open http://localhost:5173 in Chrome.

5. Next Steps
Implement the "Run Agent" button to trigger 
main.py
 from the UI.
Add "Corpus Import" functionality to upload files via the web interface.

7. v1.1.0 Enhancements (Implemented)
- **Evidence Context**: Added `/api/passages/{id}` endpoint and `EvidenceChip` component in Dossier to reveal passage text on hover.
- **Alias Resolution**: Added `/api/aliases` endpoint and updated Entity Explorer to display known aliases.
- **TDD Compliance**: Backend features verified with `tests/test_server_api.py`.

6. Protocol for Future Work
IMPORTANT

Test-Driven Development (TDD) Requirement For all future feature implementations (e.g., File Import, Agent Control), you MUST follow TDD practices:

Write the test first: Define the interface and expected behavior in a test file (e.g., tests/test_importer.py).
Run the test: specific failure confirms the missing feature.
Implement the code: Write the minimum class/method to pass the test, focusing on solid OOP principles (encapsulation, single responsibility).
Refactor: Improve the design while keeping tests green.
This approach is mandatory to ensure robust Object-Oriented Design as the system grows.
