# Construction: design decisions and traceability

AI-DLC means **AI-Driven Development Life Cycle**, a development methodology. The four-agent runtime is the product architecture. These lifecycle documents adapt its inception/construction/operations separation; they do not assert formal certification or execution of the entire AWS AI-DLC workflow.

| Requirement | Implementation | Verification |
|---|---|---|
| Grounded diagnosis | app/server.py result + app/agents/tools.py | Existing feature/model tests and ground-truth exclusion checks |
| Four logical agents | app/agents/prompts.py + runtime.py | Real SDK types with simulated provider tool responses |
| Selective follow-ups | Coordinator function-call routing | One-specialist follow-up test |
| Explicit costs | Deterministic cost_scenario reused by energy tool | Independent unit arithmetic and server recomputation |
| Interactive UI | app/static/agents.js + index.html + style.css | Syntax/static checks; manual acceptance guide; browser QA pending |
| Historical replay | Original display samples, slider/play/speed | Source sample invariants; manual playback acceptance pending |
| Reviewable draft | Server-owned checklist and browser acknowledgement | Draft status tests; manual export acceptance pending |
| Bounded execution | Calls, deadline, allowlists, semaphore | Budget/deadline/unknown/repeated tools and busy route tests |
| No fake AI success | Explicit 503/502 errors; no fallback | Provider failure and missing-configuration tests |
| Delivery | Scripts and ZIP checksum inventory | Test suite, deployment dry-run, ZIP integrity and hash checks |

Decisions: preserve proven Flask/NumPy/scikit-learn implementation; introduce a dedicated agent package and frontend module. Use Google Gen AI SDK manual function calling so agent delegation and tool use are explicit. Share one configured Gemini model across four isolated role conversations. Keep calculator deterministic and support local use without an LLM.

Model response text is untrusted and rendered as plain text. Request history is bounded. Tool arguments cannot provide arbitrary code, HTTP URLs, filesystem paths or machine controls. Export acknowledgement is explicitly limited and is not treated as authenticated approval.

Methodology reference: https://aws.amazon.com/blogs/devops/building-with-ai-dlc-using-amazon-q-developer/
