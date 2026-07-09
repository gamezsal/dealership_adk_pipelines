import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

const sidebarLabels = {
  title: "Dealership QA Coordinator",
  initial: "Hi! I am ready to extract and validate deal packs. How can I help?",
};

function App() {
  return (
    // NEW: Point directly to port 8000 and explicitly select the "default" agent
    <CopilotKit runtimeUrl="http://127.0.0.1:8000/api/copilotkit/" agent="0">

      <CopilotSidebar
        defaultOpen={true}
        labels={sidebarLabels}
      >
        <div style={{ padding: "2rem", fontFamily: "sans-serif", textAlign: "center" }}>
          <h1>Dealership QA & Provenance</h1>
          <p>Your multi-agent backend is successfully connected via the AG-UI protocol!</p>
        </div>
      </CopilotSidebar>

    </CopilotKit>
  );
}

export default App;