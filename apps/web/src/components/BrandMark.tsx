import React from "react";

interface BrandMarkProps {
  className?: string;
  title?: string;
}

export const BrandMark: React.FC<BrandMarkProps> = ({
  className = "w-10 h-10",
  title = "FPL Edge",
}) => (
  <svg
    viewBox="0 0 48 48"
    role="img"
    aria-label={title}
    className={className}
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <title>{title}</title>
    <rect x="2" y="2" width="44" height="44" rx="9" fill="#A8D741" />
    <path d="M13 11V37H34" stroke="#111713" strokeWidth="4" strokeLinecap="square" />
    <path d="M14 14H35M14 24H31M14 34H35" stroke="#111713" strokeWidth="4" />
    <circle cx="35" cy="24" r="3" fill="#F4F1E8" stroke="#111713" strokeWidth="2" />
  </svg>
);
