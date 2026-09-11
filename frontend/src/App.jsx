import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DataEntry from './pages/DataEntry';
import TimetablePage from './pages/Timetable';

const PAGE_TITLES = {
  '/':          'Dashboard',
  '/data':      'Data Entry',
  '/timetable': 'Generated Timetable',
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={
        <Layout title="Dashboard">
          <Dashboard />
        </Layout>
      } />
      <Route path="/data" element={
        <Layout title="Data Entry">
          <DataEntry />
        </Layout>
      } />
      <Route path="/timetable" element={
        <Layout title="Generated Timetable">
          <TimetablePage />
        </Layout>
      } />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
