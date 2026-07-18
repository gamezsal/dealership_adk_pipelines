const express = require('express');
const cors = require('cors');
// Import legacy v1 helpers directly from the root of @copilotkit/runtime
const {
    CopilotRuntime,
    copilotRuntimeNodeExpressEndpoint,
    ExperimentalEmptyAdapter
} = require('@copilotkit/runtime');
// Keep this subpath import exactly as is, as requested by the v1 deprecation warning
const { LangGraphHttpAgent } = require('@copilotkit/runtime/langgraph');

const app = express();

// 🟢 FIXED: Enable CORS for both localhost and 127.0.0.1 to avoid browser blocks
app.use(cors({
    origin: ["http://localhost:5173", "http://127.0.0.1:5173"],
    credentials: true
}));

// Initialize the CopilotRuntime and register your Python agent
const runtime = new CopilotRuntime({
    agents: {
        default: new LangGraphHttpAgent({
            // 🟢 FIXED: Forcing IPv4 prevents connection refused errors on Windows
            url: "http://127.0.0.1:8000/api/copilotkit",
        }),
    },
});

const serviceAdapter = new ExperimentalEmptyAdapter();
const copilotHandler = copilotRuntimeNodeExpressEndpoint({
    runtime,
    serviceAdapter,
    endpoint: '/api/copilotkit',
});

// Bind the middleware to Express
app.use(copilotHandler);

const PORT = 4000;
app.listen(PORT, () => {
    console.log(`\n================================================================`);
    // 🟢 FIXED: Updated terminal instructions to use the stable IPv4 loopback
    console.log(`🚀 Stateful Copilot Runtime is live at http://127.0.0.1:${PORT}/api/copilotkit`);
    console.log(`🔌 Bridging React (Port 5173) ──► Node (Port 4000) ──► Python (Port 8000)`);
    console.log(`================================================================\n`);
});