import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export const AdminRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { role, isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (role !== 'admin') {
    // If citizen tries to access admin route, redirect to citizen dashboard
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

