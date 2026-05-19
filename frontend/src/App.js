import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Shell from "./components/Shell";
import Dashboard from "./pages/Dashboard";
import PathwayConfig from "./pages/PathwayConfig";
import RunProgress from "./pages/RunProgress";
import PathwayResults from "./pages/PathwayResults";
import EmailReview from "./pages/EmailReview";
import APIsPage from "./pages/APIsPage";
import IntegrationsPage from "./pages/IntegrationsPage";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route element={<Shell />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/pathways/new" element={<PathwayConfig />} />
            <Route path="/pathways/:id/edit" element={<PathwayConfig />} />
            <Route path="/pathways/:id/run" element={<RunProgress />} />
            <Route path="/pathways/:id/results" element={<PathwayResults />} />
            <Route path="/pathways/:id/emails" element={<EmailReview />} />
            <Route path="/apis" element={<APIsPage />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;