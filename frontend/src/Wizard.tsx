import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, Sparkles } from "lucide-react";
import { Section } from "./App";

interface Props {
  sections: Section[];
  setSections: React.Dispatch<React.SetStateAction<Section[]>>;
  setReportMd: React.Dispatch<React.SetStateAction<string>>;
}

type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error' | 'reconnecting';

interface SSEError {
  type: 'connection' | 'cors' | 'timeout' | 'server';
  message: string;
  details?: string;
}

// Input component definition (moved to top to fix hoisting issue)
const Input = ({ label, value, onChange }: any) => (
  <div>
    <label className="text-sm font-semibold mb-1 block">{label}</label>
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-slate-700 rounded px-4 py-2"
    />
  </div>
);

const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 3000, 5000]; // Progressive delays

export default function Wizard({ sections, setSections, setReportMd }: Props) {
  // 🚀 SSE FIX VERSION 2.0 - If you see this log, the new version loaded!
  console.log("🚀 SSE FIX VERSION 2.0 - Wizard component loaded with CORS fix!");
  
  const [topic, setTopic] = useState("");
  const [guidelines, setGuidelines] = useState("");
  const [sectionTitles, setSectionTitles] = useState<string[]>([""]);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [connectionError, setConnectionError] = useState<SSEError | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const evtSourceRef = useRef<EventSource | null>(null);

  // Cleanup EventSource on component unmount
  useEffect(() => {
    return () => {
      if (evtSourceRef.current) {
        evtSourceRef.current.close();
        evtSourceRef.current = null;
      }
    };
  }, []);

  const connectWithRetry = useCallback((retryAttempt = 0) => {
    if (retryAttempt >= MAX_RETRIES) {
      setConnectionState('error');
      setConnectionError({
        type: 'connection',
        message: 'Max retry attempts reached',
        details: `Failed after ${MAX_RETRIES} attempts`
      });
      setRunning(false);
      return;
    }

    const delay = RETRY_DELAYS[retryAttempt] || 5000;
    setTimeout(() => {
      setRetryCount(retryAttempt + 1);
      setConnectionState('reconnecting');
      startResearch();
    }, delay);
  }, [topic, guidelines, sectionTitles]);

  const startResearch = async () => {
    setRunning(true);
    setConnectionState('connecting');
    setConnectionError(null);
    
    const titles = sectionTitles.filter((t) => t.trim());
    const params = new URLSearchParams({
      topic,
      guidelines,
      sections: titles.join(","),
    });

    try {
      // Close existing connection
      if (evtSourceRef.current) {
        evtSourceRef.current.close();
      }

      const sseUrl = `/sse?${params}`;
      console.log("🚀 FIXED VERSION - Creating EventSource with URL:", sseUrl);
      console.log("🚀 FIXED VERSION - Full URL will resolve to:", window.location.origin + sseUrl);
      console.log("🚀 FIXED VERSION - This should NOT contain localhost:8000!");
      
      const evtSource = new EventSource(sseUrl);
      evtSourceRef.current = evtSource;

      evtSource.onopen = () => {
        console.log('SSE connection opened');
        setConnectionState('connected');
        setConnectionError(null);
        setRetryCount(0);
      };

      evtSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          console.log("SSE Event received:", data);

          // Handle different event types
          switch (data.type) {
            case "status":
              setStatus(data.message || "Processing...");
              setProgress(data.progress || 0);
              console.log(
                "Status:",
                data.message,
                `Progress: ${data.progress}%`,
              );
              break;

            case "section_start":
              setStatus(`Researching: ${data.section}`);
              setProgress(data.progress || 0);
              console.log(`Starting section: ${data.section}`);
              break;

            case "section_complete":
              // Use functional update to prevent race conditions
              setSections(prev => {
                const existing = prev.find(s => s.title === data.section);
                if (existing) return prev; // Prevent duplicates
                const newSection: Section = {
                  title: data.section,
                  content: data.content || "",
                  sources: data.sources || [],
                };
                return [...prev, newSection];
              });
              setStatus(`Completed: ${data.section}`);
              setProgress(data.progress || 0);
              console.log(`Section completed: ${data.section}`);
              break;

            case "section_error":
              console.error(`Section failed: ${data.section}`, data.error);
              // Could add error display here
              break;

            case "report_complete":
              // Set the final report markdown
              setReportMd(data.content || "");
              setRunning(false);
              setConnectionState('disconnected');
              evtSource.close();
              console.log("Report complete!");
              break;

            case "error":
              console.error("Research error:", data.message);
              setConnectionState('error');
              setConnectionError({
                type: 'server',
                message: data.message || 'Research failed',
                details: 'Server encountered an error during research'
              });
              evtSource.close();
              setRunning(false);
              break;

            default:
              console.warn("Unknown event type:", data.type);
          }
        } catch (err) {
          console.error("Failed to parse SSE event:", err);
          setConnectionError({
            type: 'server',
            message: 'Invalid server response format',
            details: String(err)
          });
        }
      };

      evtSource.onerror = (err) => {
        console.error("SSE connection error details:", {
          error: err,
          readyState: evtSource.readyState,
          url: evtSource.url,
          withCredentials: evtSource.withCredentials
        });
        
        // Log the actual URL being used
        console.log("EventSource URL being used:", evtSource.url);
        console.log("EventSource readyState:", evtSource.readyState, "(0=CONNECTING, 1=OPEN, 2=CLOSED)");
        
        if (evtSource.readyState === EventSource.CLOSED) {
          setConnectionState('error');
          setConnectionError({
            type: 'connection',
            message: 'Connection closed by server',
            details: `Server terminated connection. URL: ${evtSource.url}`
          });
        } else if (evtSource.readyState === EventSource.CONNECTING) {
          setConnectionState('reconnecting');
          setConnectionError({
            type: 'connection',
            message: 'Attempting to reconnect...',
            details: `Connection lost, retrying. URL: ${evtSource.url}`
          });
        }
        
        setRunning(false);
      };

    } catch (err) {
      console.error("Failed to start research:", err);
      setRunning(false);
      setConnectionState('error');
      setConnectionError({
        type: 'cors',
        message: 'Failed to establish connection',
        details: String(err)
      });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 60 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -60 }}
      className="flex flex-col items-center justify-center p-8"
    >
      <motion.h1
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        className="text-5xl font-black bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400 mb-10"
      >
        Smart Research Crew
      </motion.h1>
      <motion.div
        layout
        className="w-full max-w-2xl space-y-6 bg-slate-800/60 backdrop-blur-md rounded-2xl p-8 shadow-2xl"
      >
        <Input label="Research topic" value={topic} onChange={setTopic} />
        <Input
          label="Guidelines / tone"
          value={guidelines}
          onChange={setGuidelines}
        />
        <div>
          <label className="text-sm font-semibold mb-2 block">Sections</label>
          {sectionTitles.map((t, i) => (
            <motion.div key={i} layout className="flex items-center gap-2 mb-2">
              <input
                className="flex-1 bg-slate-700 rounded px-3 py-2"
                value={t}
                onChange={(e) => {
                  const next = [...sectionTitles];
                  next[i] = e.target.value;
                  setSectionTitles(next);
                }}
                placeholder={`Section ${i + 1}`}
              />
              <button
                onClick={() =>
                  setSectionTitles(sectionTitles.filter((_, idx) => idx !== i))
                }
                className="text-red-400 hover:text-red-300"
              >
                <Trash2 size={18} />
              </button>
            </motion.div>
          ))}
          <button
            onClick={() => setSectionTitles([...sectionTitles, ""])}
            className="text-sm text-purple-300 flex items-center gap-1"
          >
            <Plus size={14} /> Add section
          </button>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          disabled={running || !topic}
          onClick={startResearch}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 font-bold rounded-xl py-3 disabled:opacity-50"
        >
          {running ? <Sparkles className="animate-spin" /> : <Sparkles />}
          {running ? "Agents at work…" : "Launch Research"}
        </motion.button>

        {/* Connection Status Indicator */}
        {(running || connectionState !== 'disconnected') && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-4 p-3 bg-slate-700/50 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${
                connectionState === 'connected' ? 'bg-green-400 animate-pulse' : 
                connectionState === 'connecting' || connectionState === 'reconnecting' ? 'bg-yellow-400 animate-pulse' : 
                'bg-red-400'
              }`} />
              <span className="text-sm">
                {connectionState === 'connected' && 'Connected to research service'}
                {connectionState === 'connecting' && 'Connecting to research service...'}
                {connectionState === 'reconnecting' && 'Reconnecting...'}
                {connectionState === 'error' && 'Connection failed'}
              </span>
            </div>
            
            {connectionError && (
              <div className="mt-2 text-xs text-red-300">
                <strong>{connectionError.type.toUpperCase()}:</strong> {connectionError.message}
                {connectionError.details && (
                  <div className="text-slate-400 mt-1">{connectionError.details}</div>
                )}
                {connectionState === 'error' && retryCount < MAX_RETRIES && (
                  <button
                    onClick={() => connectWithRetry(retryCount)}
                    className="mt-2 px-3 py-1 bg-purple-600 hover:bg-purple-700 rounded text-white text-xs"
                  >
                    Retry Connection ({retryCount}/{MAX_RETRIES})
                  </button>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* Progress and Status Display */}
        {running && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-6 space-y-3"
          >
            {/* Progress Bar */}
            <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>

            {/* Status Text */}
            <p className="text-center text-sm text-slate-300">
              {status || "Initializing research..."}
            </p>

            {/* Section Results Preview */}
            {sections.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-xs text-slate-400 uppercase tracking-wide">
                  Completed Sections ({sections.length})
                </p>
                {sections.map((section, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="bg-slate-700/50 rounded px-3 py-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">
                        {section.title}
                      </span>
                      <span className="text-xs text-green-400">✓</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
}
