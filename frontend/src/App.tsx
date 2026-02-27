import { lazy, Suspense } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import Landing from "./pages/Landing";
import NotFound from "./pages/NotFound";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Analyze = lazy(() => import("./pages/Analyze"));
const DealResults = lazy(() => import("./pages/DealResults"));
const DealsList = lazy(() => import("./pages/DealsList"));
const Chat = lazy(() => import("./pages/Chat"));
const MarketComparison = lazy(() => import("./pages/MarketComparison"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-section-bg">
        <NavBar />
        <Suspense
          fallback={
            <div className="flex min-h-screen items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-primary border-t-transparent" />
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/deals" element={<DealsList />} />
            <Route path="/deals/preview" element={<DealResults />} />
            <Route path="/deals/:id" element={<DealResults />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/markets" element={<MarketComparison />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </div>
    </Router>
  );
}

export default App;
