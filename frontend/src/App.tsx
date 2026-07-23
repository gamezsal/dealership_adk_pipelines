import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

const sidebarLabels = {
  title: "Dealership QA Coordinator",
  initial: "Hi! I am ready to extract and validate deal packs. How can I help?",
};

function App() {
  return (
    // Pointing to your proxy path and selecting the "default" agent
    <CopilotKit runtimeUrl="http://localhost:4000/api/copilotkit/" agent="default">

      <CopilotSidebar
        defaultOpen={true}
        labels={sidebarLabels}
        // 🟢 STEP 1: Enable the native sidebar attachment paperclip & drop-zone
        imageUploadsEnabled={true}
        // 🟢 STEP 2: Configure the drop-zone to accept PDFs specifically
        inputFileAccept="application/pdf"
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