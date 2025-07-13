import React from "react";
import { Bell } from "lucide-react";

export default function Header() {
  return (
    <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#e7edf4] px-10 py-3">
      <div className="flex items-center gap-4 text-[#0d141c]">
        <div className="size-4">
          <svg
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g clipPath="url(#clip0_6_319)">
              <path
                d="M8.57829 8.57829C5.52816 11.6284 3.451 15.5145 2.60947 19.7452C1.76794 23.9758 2.19984 28.361 3.85056 32.3462C5.50128 36.3314 8.29667 39.7376 11.8832 42.134C15.4698 44.5305 19.6865 45.8096 24 45.8096C28.3135 45.8096 32.5302 44.5305 36.1168 42.134C39.7033 39.7375 42.4987 36.3314 44.1494 32.3462C45.8002 28.361 46.2321 23.9758 45.3905 19.7452C44.549 15.5145 42.4718 11.6284 39.4217 8.57829L24 24L8.57829 8.57829Z"
                fill="currentColor"
              />
            </g>
            <defs>
              <clipPath id="clip0_6_319">
                <rect width="48" height="48" fill="white" />
              </clipPath>
            </defs>
          </svg>
        </div>
        <h2 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em]">
          Research Reports
        </h2>
      </div>
      <div className="flex flex-1 justify-end gap-8">
        <div className="flex items-center gap-9">
          <a
            className="text-[#0d141c] text-sm font-medium leading-normal"
            href="#"
          >
            Dashboard
          </a>
          <a
            className="text-[#0d141c] text-sm font-medium leading-normal"
            href="#"
          >
            Reports
          </a>
          <a
            className="text-[#0d141c] text-sm font-medium leading-normal"
            href="#"
          >
            Templates
          </a>
          <a
            className="text-[#0d141c] text-sm font-medium leading-normal"
            href="#"
          >
            Help
          </a>
        </div>
        <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 bg-[#e7edf4] text-[#0d141c] gap-2 text-sm font-bold leading-normal tracking-[0.015em] min-w-0 px-2.5">
          <Bell size={20} />
        </button>
        <div
          className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10"
          style={{
            backgroundImage: `url("https://lh3.googleusercontent.com/aida-public/AB6AXuBEfho80FmBGw565iGin94vXpv9_373rNRYD-F-Cj1pZRsR9KzwT7SMT4CzsogtV8x22kUPYN4xoYruRiUzJhZB4ydgjGgEVJmyq7pqIUmbYRBr_L_erhQTIWLeK77T6H0-iKaU0zDZ9TcOzuKtRHWco7oHMnRC20JA48tltumVCFuY-c7BrQhKcCRABUOAWUb9RIQX6b-ZEv181FdLQ1I-8-j9kk-oH0JGe6QA8MtEqSPSx6YMXhgq25rJFqYlniqcMr4FN0ZskXs")`,
          }}
        />
      </div>
    </header>
  );
}
