import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Wizard from "./Wizard";
import Report from "./Report";

export type Section = { title: string; content: string; sources: { url: string; title: string }[] };

export default function App() {
  const [sections, setSections] = useState<Section[]>([]);
  const [reportMd, setReportMd] = useState("");

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <AnimatePresence mode="wait">
        {!reportMd ? (
          <Wizard key="wiz" {...{ sections, setSections, setReportMd }} />
        ) : (
          <Report key="rep" {...{ reportMd, sections }} />
        )}
      </AnimatePresence>
    </div>
  );
}
