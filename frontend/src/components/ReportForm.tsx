import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Section } from "../App";

interface Props {
  sections: Section[];
  setSections: React.Dispatch<React.SetStateAction<Section[]>>;
  setReportMd: (reportContent: string) => void;
  currentStep: number;
  setCurrentStep: React.Dispatch<React.SetStateAction<number>>;
}

type ConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error"
  | "reconnecting";

interface SSEError {
  type: "connection" | "cors" | "timeout" | "server";
  message: string;
  details?: string;
}

const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 3000, 5000];

export default function ReportForm({
  sections,
  setSections,
  setReportMd,
  currentStep,
}: Props) {
  const [topic, setTopic] = useState("");
  const [guidelines, setGuidelines] = useState("");
  const [tone, setTone] = useState("");
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [connectionError, setConnectionError] = useState<SSEError | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const evtSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    return () => {
      if (evtSourceRef.current) {
        evtSourceRef.current.close();
        evtSourceRef.current = null;
      }
    };
  }, []);

  const connectWithRetry = useCallback(
    (retryAttempt = 0) => {
      if (retryAttempt >= MAX_RETRIES) {
        setConnectionState("error");
        setConnectionError({
          type: "connection",
          message: "Max retry attempts reached",
          details: `Failed after ${MAX_RETRIES} attempts`,
        });
        setRunning(false);
        return;
      }

      const delay = RETRY_DELAYS[retryAttempt] || 5000;
      setTimeout(() => {
        setRetryCount(retryAttempt + 1);
        setConnectionState("reconnecting");
        startResearch();
      }, delay);
    },
    [topic, guidelines],
  );

  const startResearch = async () => {
    setRunning(true);
    setConnectionState("connecting");
    setConnectionError(null);

    const params = new URLSearchParams({
      topic,
      guidelines: guidelines || "",
      sections: "Introduction,Main Analysis,Conclusion", // Default sections
    });

    try {
      if (evtSourceRef.current) {
        evtSourceRef.current.close();
      }

      const sseUrl = `/sse?${params}`;
      const evtSource = new EventSource(sseUrl);
      evtSourceRef.current = evtSource;

      evtSource.onopen = () => {
        setConnectionState("connected");
        setConnectionError(null);
        setRetryCount(0);
      };

      evtSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);

          switch (data.type) {
            case "status":
              setStatus(data.message || "Processing...");
              setProgress(data.progress || 0);
              break;

            case "section_start":
              setStatus(`Researching: ${data.section}`);
              setProgress(data.progress || 0);
              break;

            case "section_complete":
              setSections((prev) => {
                const existing = prev.find((s) => s.title === data.section);
                if (existing) return prev;
                const newSection: Section = {
                  title: data.section,
                  content: data.content || "",
                  sources: data.sources || [],
                };
                return [...prev, newSection];
              });
              setStatus(`Completed: ${data.section}`);
              setProgress(data.progress || 0);
              break;

            case "report_complete":
              setReportMd(data.content || "");
              setRunning(false);
              setConnectionState("disconnected");
              evtSource.close();
              break;

            case "error":
              setConnectionState("error");
              setConnectionError({
                type: "server",
                message: data.message || "Research failed",
                details: "Server encountered an error during research",
              });
              evtSource.close();
              setRunning(false);
              break;
          }
        } catch (err) {
          setConnectionError({
            type: "server",
            message: "Invalid server response format",
            details: String(err),
          });
        }
      };

      evtSource.onerror = () => {
        setConnectionState("error");
        setConnectionError({
          type: "connection",
          message: "Connection failed",
          details: "Unable to connect to research service",
        });
        setRunning(false);
      };
    } catch (err) {
      setRunning(false);
      setConnectionState("error");
      setConnectionError({
        type: "cors",
        message: "Failed to establish connection",
        details: String(err),
      });
    }
  };

  const handleNext = () => {
    if (currentStep === 1 && topic.trim()) {
      startResearch();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="flex flex-wrap justify-between gap-3 p-4">
        <p className="text-[#0d141c] tracking-light text-[32px] font-bold leading-tight min-w-72">
          Create a new report
        </p>
      </div>

      <h3 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] px-4 pb-2 pt-4">
        Step 1 of 3: Report Topic
      </h3>

      <div className="flex max-w-[480px] flex-wrap items-end gap-4 px-4 py-3">
        <label className="flex flex-col min-w-40 flex-1">
          <p className="text-[#0d141c] text-base font-medium leading-normal pb-2">
            Report Topic
          </p>
          <input
            placeholder="Enter the topic of your report"
            className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#0d141c] focus:outline-0 focus:ring-0 border-none bg-[#e7edf4] focus:border-none h-14 placeholder:text-[#49739c] p-4 text-base font-normal leading-normal"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
        </label>
      </div>

      <div className="flex max-w-[480px] flex-wrap items-end gap-4 px-4 py-3">
        <label className="flex flex-col min-w-40 flex-1">
          <p className="text-[#0d141c] text-base font-medium leading-normal pb-2">
            Guidelines (Optional)
          </p>
          <textarea
            placeholder="Add any specific guidelines or requirements for the report"
            className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#0d141c] focus:outline-0 focus:ring-0 border-none bg-[#e7edf4] focus:border-none min-h-36 placeholder:text-[#49739c] p-4 text-base font-normal leading-normal"
            value={guidelines}
            onChange={(e) => setGuidelines(e.target.value)}
          />
        </label>
      </div>

      <div className="flex max-w-[480px] flex-wrap items-end gap-4 px-4 py-3">
        <label className="flex flex-col min-w-40 flex-1">
          <p className="text-[#0d141c] text-base font-medium leading-normal pb-2">
            Tone (Optional)
          </p>
          <select
            className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#0d141c] focus:outline-0 focus:ring-0 border-none bg-[#e7edf4] focus:border-none h-14 bg-[image:--select-button-svg] placeholder:text-[#49739c] p-4 text-base font-normal leading-normal"
            value={tone}
            onChange={(e) => setTone(e.target.value)}
          >
            <option value="">Select tone (optional)</option>
            <option value="professional">Professional</option>
            <option value="casual">Casual</option>
            <option value="academic">Academic</option>
            <option value="technical">Technical</option>
          </select>
        </label>
      </div>

      {/* Progress Display */}
      {running && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="px-4 py-3"
        >
          <div className="max-w-[480px] bg-[#e7edf4] rounded-lg p-4">
            <div className="w-full bg-slate-300 rounded-full h-2 overflow-hidden mb-3">
              <motion.div
                className="h-full bg-[#3d98f4]"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <p className="text-[#0d141c] text-sm">
              {status || "Initializing research..."}
            </p>

            {/* Connection Status */}
            <div className="flex items-center gap-2 mt-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  connectionState === "connected"
                    ? "bg-green-500"
                    : connectionState === "connecting" ||
                        connectionState === "reconnecting"
                      ? "bg-yellow-500"
                      : "bg-red-500"
                }`}
              />
              <span className="text-xs text-[#49739c]">
                {connectionState === "connected" && "Connected"}
                {connectionState === "connecting" && "Connecting..."}
                {connectionState === "reconnecting" && "Reconnecting..."}
                {connectionState === "error" && "Connection failed"}
              </span>
            </div>

            {connectionError && (
              <div className="mt-2 text-xs text-red-600">
                {connectionError.message}
                {connectionState === "error" && retryCount < MAX_RETRIES && (
                  <button
                    onClick={() => connectWithRetry(retryCount)}
                    className="ml-2 text-[#3d98f4] underline"
                  >
                    Retry ({retryCount}/{MAX_RETRIES})
                  </button>
                )}
              </div>
            )}

            {/* Completed Sections */}
            {sections.length > 0 && (
              <div className="mt-3">
                <p className="text-xs text-[#49739c] mb-1">
                  Completed Sections ({sections.length})
                </p>
                {sections.map((section, idx) => (
                  <div key={idx} className="text-xs text-[#0d141c] mb-1">
                    ✓ {section.title}
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}

      <div className="flex px-4 py-3 justify-end">
        <button
          className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-[#3d98f4] text-slate-50 text-sm font-bold leading-normal tracking-[0.015em] disabled:opacity-50"
          onClick={handleNext}
          disabled={running || !topic.trim()}
        >
          <span className="truncate">
            {running ? "Researching..." : "Next"}
          </span>
        </button>
      </div>
    </motion.div>
  );
}
