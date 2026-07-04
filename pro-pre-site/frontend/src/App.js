import React from "react";
import "@/App.css";
import "@/i18n";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Toaster } from "@/components/ui/sonner";

import Header from "@/components/site/Header";
import Footer from "@/components/site/Footer";
import FloatingActions from "@/components/site/FloatingActions";
import ChatWidget from "@/components/site/ChatWidget";

import Home from "@/pages/Home";
import Booking from "@/pages/Booking";
import Defi from "@/pages/Defi";
import AdminLogin from "@/pages/AdminLogin";
import AdminDashboard from "@/pages/AdminDashboard";
import AuthCallback from "@/pages/AuthCallback";
import MonEspace from "@/pages/MonEspace";
import PaymentSuccess from "@/pages/PaymentSuccess";
import Privacy from "@/pages/Privacy";
import MentionsLegales from "@/pages/MentionsLegales";
import CGV from "@/pages/CGV";
import Reglement from "@/pages/Reglement";
import CookieBanner from "@/components/site/CookieBanner";

function AppRouter() {
  const location = useLocation();
  const { i18n } = useTranslation();

  React.useEffect(() => {
    if (i18n.language) document.documentElement.lang = i18n.language.slice(0,2);
  }, [i18n.language]);

  // Handle Emergent Auth callback synchronously during render to avoid race conditions
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <>
      <Header />
      <main className="min-h-[60vh]">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/booking" element={<Booking />} />
          <Route path="/defi" element={<Defi />} />
          <Route path="/login" element={<AdminLogin />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/mon-espace" element={<MonEspace />} />
          <Route path="/payment/success" element={<PaymentSuccess />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/mentions-legales" element={<MentionsLegales />} />
          <Route path="/cgv" element={<CGV />} />
          <Route path="/reglement" element={<Reglement />} />
        </Routes>
      </main>
      <Footer />
      <FloatingActions />
      <ChatWidget />
      <CookieBanner />
    </>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AppRouter />
        <Toaster richColors position="top-center" />
      </BrowserRouter>
    </div>
  );
}

export default App;
