import React, { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, Sparkles } from "lucide-react";
import { Section } from "./App";

interface Props {
  setSections: React.Dispatch<React.SetStateAction<Section[]>>;
  setReportMd: React.Dispatch<React.SetStateAction<string>>;
}

// Input component definition (moved to top to fix hoisting issue)
const Input = ({ label, value, onChange }: any) => (
  <div>
    <label className="text-sm font-semibold mb-1 block">{label}</label>
    <input value={value} onChange={(e) => onChange(e.target.value)} className="w-full bg-slate-700 rounded px-4 py-2" />
  </div>
);

export default function Wizard({ setSections, setReportMd }: Props) {
  const [topic, setTopic] = useState("");
  const [guidelines, setGuidelines] = useState("");
  const [sectionTitles, setSectionTitles] = useState<string[]>([""]);
  const [running, setRunning] = useState(false);

  const startResearch = async () => {
    setRunning(true);
    const titles = sectionTitles.filter((t) => t.trim());
    const params = new URLSearchParams({ topic, guidelines, sections: titles.join(",") });
    const evtSource = new EventSource(`http://localhost:8000/sse?${params}`);
    const tempSections: Section[] = [];

    evtSource.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "section") {
        tempSections.push(data.payload);
        setSections([...tempSections]);
      }
      if (data.type === "report") {
        setReportMd(data.payload);
        evtSource.close();
      }
    };
  };

  return (
    <motion.div initial={{ opacity: 0, y: 60 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -60 }} className="flex flex-col items-center justify-center p-8">
      <motion.h1 initial={{ scale: 0.8 }} animate={{ scale: 1 }} className="text-5xl font-black bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400 mb-10">
        Smart Research Crew
      </motion.h1>
      <motion.div layout className="w-full max-w-2xl space-y-6 bg-slate-800/60 backdrop-blur-md rounded-2xl p-8 shadow-2xl">
        <Input label="Research topic" value={topic} onChange={setTopic} />
        <Input label="Guidelines / tone" value={guidelines} onChange={setGuidelines} />
        <div>
          <label className="text-sm font-semibold mb-2 block">Sections</label>
          {sectionTitles.map((t, i) => (
            <motion.div key={i} layout className="flex items-center gap-2 mb-2">
              <input className="flex-1 bg-slate-700 rounded px-3 py-2" value={t} onChange={(e) => { const next = [...sectionTitles]; next[i] = e.target.value; setSectionTitles(next); }} placeholder={`Section ${i + 1}`} />
              <button onClick={() => setSectionTitles(sectionTitles.filter((_, idx) => idx !== i))} className="text-red-400 hover:text-red-300"><Trash2 size={18} /></button>
            </motion.div>
          ))}
          <button onClick={() => setSectionTitles([...sectionTitles, ""])} className="text-sm text-purple-300 flex items-center gap-1"><Plus size={14} /> Add section</button>
        </div>
        <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} disabled={running || !topic} onClick={startResearch} className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 font-bold rounded-xl py-3 disabled:opacity-50">
          {running ? <Sparkles className="animate-spin" /> : <Sparkles />}
          {running ? "Agents at work…" : "Launch Research"}
        </motion.button>
      </motion.div>
    </motion.div>
);


}
