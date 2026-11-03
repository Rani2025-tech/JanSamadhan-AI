import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider } from './context/LanguageContext';
import { AccessibilityProvider } from './context/AccessibilityContext';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import { ComplaintProvider } from './context/ComplaintContext';

import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { MyComplaints } from './pages/MyComplaints';
import { ComplaintDetail } from './pages/ComplaintDetail';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { FileComplaintForm } from './pages/FileComplaintForm';
import { NotificationsPage } from './pages/NotificationsPage';
import { ProfilePage } from './pages/ProfilePage';
import { AdminDashboard } from './pages/AdminDashboard';
import { AdminComplaints } from './pages/AdminComplaints';
import { HotspotMap } from './pages/HotspotMap';
import { ImpactPage } from './pages/ImpactPage';

import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AdminRoute } from './components/auth/AdminRoute';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AccessibilityProvider>
          <AuthProvider>
            <NotificationProvider>
              <ComplaintProvider>
                <Routes>
                  {/* Public Login Route */}
                  <Route path="/login" element={<Login />} />
                  <Route path="/terms" element={<div className="min-h-screen bg-cream-100 p-8 max-w-2xl mx-auto space-y-4"><h1 className="text-2xl font-bold text-maroon-800">Terms of Service</h1><p className="text-gray-700">JanSamadhan citizen grievance redressal platform terms and conditions.</p><a href="/login" className="text-maroon-800 underline font-semibold">&larr; Back to Login</a></div>} />
                  <Route path="/privacy" element={<div className="min-h-screen bg-cream-100 p-8 max-w-2xl mx-auto space-y-4"><h1 className="text-2xl font-bold text-maroon-800">Privacy Policy</h1><p className="text-gray-700">JanSamadhan data protection and grievance privacy policy.</p><a href="/login" className="text-maroon-800 underline font-semibold">&larr; Back to Login</a></div>} />

                  {/* Protected Citizen & Guest Routes inside Main Layout */}
                  <Route
                    path="/"
                    element={
                      <ProtectedRoute>
                        <AppLayout />
                      </ProtectedRoute>
                    }
                  >
                    <Route index element={<Navigate to="/dashboard" replace />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="assistant" element={<AIAssistantPage />} />
                    <Route path="complaints" element={<MyComplaints />} />
                    <Route path="complaints/:id" element={<ComplaintDetail />} />
                    <Route path="file-form" element={<FileComplaintForm />} />
                    <Route path="notifications" element={<NotificationsPage />} />
                    <Route path="profile" element={<ProfilePage />} />
                    <Route path="impact" element={<ImpactPage />} />

                    {/* Admin Restricted Routes */}
                    <Route
                      path="hotspots"
                      element={
                        <AdminRoute>
                          <HotspotMap />
                        </AdminRoute>
                      }
                    />
                    <Route
                      path="admin"
                      element={
                        <AdminRoute>
                          <AdminDashboard />
                        </AdminRoute>
                      }
                    />
                    <Route
                      path="admin/complaints"
                      element={
                        <AdminRoute>
                          <AdminComplaints />
                        </AdminRoute>
                      }
                    />
                  </Route>

                  {/* Fallback */}
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </ComplaintProvider>
            </NotificationProvider>
          </AuthProvider>
        </AccessibilityProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
};

export default App;

