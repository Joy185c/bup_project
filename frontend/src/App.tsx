import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Layout } from './components/layout/Layout';

// Pages
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import OptimizePage from './pages/OptimizePage';
import EnergyPlanPage from './pages/EnergyPlanPage';
import AnalyticsPage from './pages/AnalyticsPage';
import HistoryPage from './pages/HistoryPage';

function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{ className: 'font-sans' }} />
      <Routes>
        {/* Landing / Hero Page */}
        <Route path="/" element={<LandingPage />} />

        {/* Dedicated Control Center / App Routes */}
        <Route element={<Layout />}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="optimize" element={<OptimizePage />} />
          <Route path="plan" element={<EnergyPlanPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="history" element={<HistoryPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
