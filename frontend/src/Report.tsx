import React from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowLeft } from "lucide-react";
import { Section } from "./App";

interface Props {
  reportMd: string;
  sections: Section[];
}

export default function Report({ reportMd, sections }: Props) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl mx-auto p-8">
      <button onClick={() => window.location.reload()} className="flex items-center gap-2 text-purple-300 mb-6 hover:text-purple-200">
        <ArrowLeft size={18} /> New Research
      </button>
      <motion.article initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="prose prose-invert prose-lg">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{reportMd}</ReactMarkdown>
      </motion.article>
    </motion.div>
);
}
