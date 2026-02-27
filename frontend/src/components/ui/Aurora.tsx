import type { CSSProperties } from "react";

interface AuroraProps {
  children: React.ReactNode;
  className?: string;
}

const cssKeyframes = `
@keyframes aurora-float-1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%       { transform: translate(40px, -60px) scale(1.1); }
  66%       { transform: translate(-30px, 30px) scale(0.95); }
}
@keyframes aurora-float-2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  40%       { transform: translate(-50px, 40px) scale(1.05); }
  70%       { transform: translate(30px, -20px) scale(0.9); }
}
@keyframes aurora-float-3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50%       { transform: translate(20px, -40px) scale(1.15); }
}
`;

const blobBase: CSSProperties = {
  position: "absolute",
  borderRadius: "50%",
  filter: "blur(80px)",
  opacity: 0.35,
};

export default function Aurora({ children, className }: AuroraProps) {
  return (
    <>
      <style>{cssKeyframes}</style>
      <div className={`relative overflow-hidden ${className ?? ""}`}>
        <div className="pointer-events-none absolute inset-0 z-0">
          <div
            style={{
              ...blobBase,
              width: 600,
              height: 600,
              background: "#2563EB",
              top: -100,
              left: -100,
              animation: "aurora-float-1 18s ease-in-out infinite",
            }}
          />
          <div
            style={{
              ...blobBase,
              width: 500,
              height: 500,
              background: "#1B2A4A",
              bottom: -100,
              right: -50,
              animation: "aurora-float-2 22s ease-in-out infinite",
            }}
          />
          <div
            style={{
              ...blobBase,
              width: 400,
              height: 400,
              background: "#7C3AED",
              top: "40%",
              right: "20%",
              animation: "aurora-float-3 15s ease-in-out infinite",
            }}
          />
        </div>
        <div className="relative z-10">{children}</div>
      </div>
    </>
  );
}
