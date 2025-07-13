import React, { useState } from "react";
import { AnimatePresence } from "framer-motion";
import LandingHeader from "./components/LandingHeader";
import Header from "./components/Header";
import LandingPage from "./components/LandingPage";
import ReportForm from "./components/ReportForm";
import Report from "./Report";

export type Section = {
  title: string;
  content: string;
  sources: { url: string; title: string }[];
};

type AppState = "landing" | "report-form" | "report-view";

export default function App() {
  const [sections, setSections] = useState<Section[]>([]);
  const [reportMd, setReportMd] = useState("");
  const [currentStep, setCurrentStep] = useState(1);
  const [appState, setAppState] = useState<AppState>("landing");

  const handleGetStarted = () => {
    setAppState("report-form");
  };

  const handleSignIn = () => {
    setAppState("report-form");
  };

  const handleReportComplete = (reportContent: string) => {
    setReportMd(reportContent);
    setAppState("report-view");
  };

  return (
    <div
      className={`relative flex size-full min-h-screen flex-col ${
        appState === "landing" ? "bg-gray-50" : "bg-slate-50"
      } group/design-root overflow-x-hidden`}
      style={{ fontFamily: 'Inter, "Noto Sans", sans-serif' }}
    >
      <div className="layout-container flex h-full grow flex-col">
        {appState === "landing" ? (
          <LandingHeader onSignIn={handleSignIn} />
        ) : (
          <Header />
        )}

        <div className="px-40 flex flex-1 justify-center py-5">
          <div className="layout-content-container flex flex-col max-w-[960px] flex-1">
            <AnimatePresence mode="wait">
              {appState === "landing" && (
                <LandingPage key="landing" onGetStarted={handleGetStarted} />
              )}
              {appState === "report-form" && (
                <ReportForm
                  key="form"
                  sections={sections}
                  setSections={setSections}
                  setReportMd={handleReportComplete}
                  currentStep={currentStep}
                  setCurrentStep={setCurrentStep}
                />
              )}
              {appState === "report-view" && (
                <Report key="rep" reportMd={reportMd} sections={sections} />
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
