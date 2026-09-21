
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
  Bot,
  Settings,
  Activity
} from "lucide-react";

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
    { id: "minileague", label: "Mini-League", icon: Trophy },
    { id: "accuracy", label: "Model Accuracy", icon: BarChart3 },
  ];

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-surface border-r border-surfaceBorder h-screen sticky top-0 z-30">
        {/* Branding Logo Header */}
        <div className="p-6 border-b border-surfaceBorder flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center font-bold text-slate-900 text-xl shadow-lg shadow-primary/20">
            <Activity className="w-6 h-6 text-slate-950" />
          </div>
          <div>
            <h1 className="font-extrabold text-xl tracking-tight text-slate-100 flex items-center gap-1.5">
              {brandName} <span className="text-xs px-1.5 py-0.5 rounded bg-primary/20 text-primary font-mono font-semibold">PRO</span>
            </h1>
            <p className="text-xs text-slate-400 font-medium">Decision Support Engine</p>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  isActive
                    ? "bg-primary text-slate-950 shadow-md shadow-primary/20"
                    : "text-slate-400 hover:text-slate-100 hover:bg-surfaceHover"
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? "text-slate-950" : "text-slate-400"}`} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Bottom AI Assistant & Settings Footer */}
        <div className="p-4 border-t border-surfaceBorder space-y-2">
          <button
            onClick={() => setActiveTab("assistant")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold border transition-all duration-200 ${
              activeTab === "assistant"
                ? "bg-secondary text-slate-950 border-secondary"
                : "border-surfaceBorder bg-surfaceHover/50 text-slate-200 hover:bg-surfaceHover"
            }`}
          >
            <Bot className="w-5 h-5 text-secondary" />
            <span>AI Assistant</span>
          </button>

          <div className="flex items-center justify-between px-4 py-2 text-xs text-slate-500 font-mono">
            <span>Model v1.0.0</span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
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
          <Bot className="w-5 h-5" />
          <span>AI Q&A</span>
        </button>
      </nav>
    </>
  );
};
