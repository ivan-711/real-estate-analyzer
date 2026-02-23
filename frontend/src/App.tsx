import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import Landing from "./pages/Landing";
import Analyze from "./pages/Analyze";
import DealResults from "./pages/DealResults";
import Login from "./pages/Login";
import Register from "./pages/Register";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-section-bg">
        <NavBar />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/deals/preview" element={<DealResults />} />
          <Route path="/deals/:id" element={<DealResults />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
