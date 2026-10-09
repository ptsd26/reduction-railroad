# Reduction Railroad frontend

Minimal frontend setup for issue #1, with the dependencies requested for future UI work.

## Getting started

Use Node.js 24 LTS and npm. From the repository root:

```sh
cd web
npm ci
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173).

## Commands

- `npm run dev`: start the development server.
- `npm run check`: run Svelte and JavaScript type checks.
- `npm run build`: create a production build.
- `npm run preview`: preview the production build locally.

## Included

- Svelte and SvelteKit, with JavaScript and JSDoc type checking.
- Tailwind CSS through its official Vite plugin.
- CodeMirror 6 with C++ language support, mounted in the browser and destroyed on unmount.
- `@xyflow/svelte` (Svelte Flow), installed for future graph development; no graph is implemented.

The demo at `/` contains a sample problem and an editable C++ snippet. The two columns stack on smaller screens. Source code stays in the editor for the current visit only. API routes are placeholders only: there is no persistence, compilation, judging, authentication, leaderboard, or progress implementation.

## API skeleton

All listed methods return HTTP `501` with the same JSON error and `Cache-Control: no-store`:

```json
{"error":{"code":"NOT_IMPLEMENTED","message":"This API endpoint is a placeholder."}}
```

| Method | Endpoint | Intended responsibility |
| --- | --- | --- |
| GET, POST | `/api/users` | List/create accounts |
| GET | `/api/users/[userId]` | Account details |
| GET | `/api/users/[userId]/progress` | Solved problems, unlocks, completion and attempts |
| GET | `/api/users/[userId]/submissions` | Read-only submission history |
| GET | `/api/problems` | Campaign problem list |
| GET | `/api/problems/[problemId]` | Problem statement and metadata |
| GET | `/api/problems/[problemId]/leaderboard` | Per-problem rankings |
| GET | `/api/leaderboard` | Global rankings |
| POST | `/api/submissions` | Future judge submission entry point |
| GET | `/api/submissions/[submissionId]` | Submission status and verdict |
| GET | `/api/submissions/[submissionId]/events` | Reserved for verdict SSE |

The events route intentionally returns the same JSON 501 response, not an active event stream. Future backend work should add authentication and authorization, input validation, pagination, database access, judge integration, and SSE lifecycle handling. These stubs do not read request bodies, execute code, or interact with a queue. The demo does not call them. No `+page.server.js` loader is needed until page data comes from the backend.

## Files

- `src/routes/+page.svelte`: demo page.
- `src/lib/CodeEditor.svelte`: browser-only editor initialization and cleanup.
- `src/routes/+layout.svelte`: shared stylesheet and favicon.
- `src/app.css`: Tailwind import and base styling.
- `vite.config.js`: SvelteKit and Tailwind configuration.

The generated adapter-auto configuration is a starting point; choose a deployment adapter when hosting is decided.
