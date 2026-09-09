import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/MainDashboard';
import Landing from './pages/Landing';
import SatelliteAnalysis from './pages/SatelliteAnalysis';
import VisualGrounding from './pages/VisualGrounding';
import ChangeDetection from './pages/ChangeDetection';
import FloodIntelligence from './pages/FloodIntelligence';
import GlacierIntelligence from './pages/GlacierIntelligence';
import LandslideIntelligence from './pages/LandslideIntelligence';
import WildfireIntelligence from './pages/WildfireIntelligence';
import DisasterIntelligence from './pages/DisasterIntelligence';
import EarlyWarningCenter from './pages/EarlyWarningCenter';
import EmergencyContacts from './pages/EmergencyContacts';
import SatelliteLocationAnalysis from './pages/SatelliteLocationAnalysis';
import LiveMonitoring from './pages/LiveMonitoring';
import LiveDetectionRiskIntelligence from './pages/LiveDetectionRiskIntelligence';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', background: '#333', color: '#fff', height: '100vh' }}>
          <h2>Something went wrong.</h2>
          <pre style={{ color: '#ff6b6b' }}>{this.state.error.toString()}</pre>
          <pre>{this.state.error.stack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

const AppLayout = () => {
  const location = useLocation();
  // Is this the 3D landing page? (Full screen, no sidebar header)
  const isLanding = location.pathname === '/';

  if (isLanding) {
    return <Routes><Route path="/" element={<Landing />} /></Routes>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-navy-dark font-sans text-slate-300">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="mx-auto max-w-7xl h-full">
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/satellite-analysis" element={<SatelliteAnalysis />} />
              <Route path="/visual-grounding" element={<VisualGrounding />} />
              <Route path="/change-detection" element={<ChangeDetection />} />
              <Route path="/flood-intelligence" element={<FloodIntelligence />} />
              <Route path="/glacier-intelligence" element={<GlacierIntelligence />} />
              <Route path="/landslide-intelligence" element={<LandslideIntelligence />} />
              <Route path="/wildfire-intelligence" element={<WildfireIntelligence />} />
              <Route path="/disaster-intelligence" element={<DisasterIntelligence />} />
              <Route path="/early-warning-center" element={<EarlyWarningCenter />} />
              <Route path="/emergency-contacts" element={<EmergencyContacts />} />
              <Route path="/location-analysis" element={<SatelliteLocationAnalysis />} />
              <Route path="/live-monitoring" element={<LiveMonitoring />} />
              <Route path="/live-risk-intelligence" element={<LiveDetectionRiskIntelligence />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AppLayout />
      </Router>
    </ErrorBoundary>
  );
}

export default App;
