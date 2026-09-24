
import React from "react";
import {
  LayoutDashboard,
  Users,
  Shuffle,
  Crown,
  Search,
  Calendar,
  Zap,
  Trophy,
  BarChart3,
  MessageSquareText,
} from "lucide-react";
import { BrandMark } from "@/components/BrandMark";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  brandName?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  brandName = "FPL Edge"
}) => {
  const navItems = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "team", label: "My Team", icon: Users },
    { id: "planner", label: "Transfer Planner", icon: Shuffle },
    { id: "captaincy", label: "Captaincy", icon: Crown },
    { id: "players", label: "Player Explorer", icon: Search },
    { id: "fixtures", label: "Fixtures", icon: Calendar },
    { id: "chips", label: "Chip Strategy", icon: Zap },
    { id: "minileague", label: "Mini-leagues", icon: Trophy },
    { id: "accuracy", label: "Model Accuracy", icon: BarChart3 },
  ];

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-60 bg-surface border-r border-surfaceBorder h-screen sticky top-0 z-30">
        {/* Branding Logo Header */}
        <div className="px-5 py-6 border-b border-surfaceBorder flex items-center gap-3">
          <BrandMark className="h-10 w-10 shrink-0" />
          <div>
            <h1 className="font-black text-lg tracking-[-0.03em] text-slate-100">{brandName}</h1>
            <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-semibold">Matchday intelligence</p>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto" aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`relative w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-semibold transition-colors ${
                  isActive
                    ? "bg-surfaceHover text-primary"
                    : "text-slate-400 hover:text-slate-100 hover:bg-surfaceHover/60"
                }`}
              >
                {isActive && <span className="absolute left-0 h-5 w-0.5 bg-primary" />}
                <Icon className={`w-4 h-4 ${isActive ? "text-primary" : "text-slate-500"}`} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Analysis assistant */}
        <div className="p-4 border-t border-surfaceBorder space-y-2">
          <button
            onClick={() => setActiveTab("assistant")}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold border transition-colors ${
              activeTab === "assistant"
                ? "bg-primary/10 text-primary border-primary/40"
                : "border-surfaceBorder bg-background/30 text-slate-300 hover:border-slate-500"
            }`}
          >
            <MessageSquareText className="w-4 h-4" />
            <span>Ask about this plan</span>
          </button>

          <div className="flex items-center justify-between px-4 py-2 text-xs text-slate-500 font-mono">
            <span>Model v2.0</span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
              Live Data
            </span>
          </div>
        </div>
      </aside>

      {/* Mobile Bottom Tab Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-surface/95 backdrop-blur-lg border-t border-surfaceBorder z-40 px-2 py-2 flex items-center justify-around">
        {navItems.slice(0, 5).map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg text-xs font-medium ${
                isActive ? "text-primary" : "text-slate-400"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label.split(" ")[0]}</span>
            </button>
          );
        })}
        <button
          onClick={() => setActiveTab("assistant")}
          className={`flex flex-col items-center gap-1 p-2 rounded-lg text-xs font-medium ${
            activeTab === "assistant" ? "text-secondary" : "text-slate-400"
          }`}
        >
          <MessageSquareText className="w-5 h-5" />
          <span>Ask</span>
        </button>
      </nav>
    </>
  );
};
