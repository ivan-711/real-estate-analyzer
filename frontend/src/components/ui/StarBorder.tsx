interface StarBorderProps {
  children: React.ReactNode;
  /** Hex or CSS color for the glowing border accent. */
  color?: string;
  /** CSS animation-duration string, e.g. "6s". */
  speed?: string;
  className?: string;
}

/**
 * Wraps children in an animated glowing border.
 * The rotating conic-gradient is clipped to a 2px gap around the content.
 *
 * Intended nesting order:
 *   <StarBorder>       ← outermost — glowing border
 *     <SpotlightCard>  ← inner — cursor spotlight
 *       card content
 *     </SpotlightCard>
 *   </StarBorder>
 */
export default function StarBorder({
  children,
  color = "#a855f7",
  speed = "6s",
  className = "",
}: StarBorderProps) {
  return (
    <div className={`relative p-[2px] rounded-xl ${className}`}>
      {/* Clipping container for the rotating gradient */}
      <div
        className="pointer-events-none absolute inset-0 rounded-xl overflow-hidden"
        aria-hidden="true"
      >
        {/* Rotating conic-gradient — centered and much larger than card */}
        <div
          className="absolute animate-spin"
          style={{
            animationDuration: speed,
            width: "300%",
            height: "300%",
            top: "-100%",
            left: "-100%",
            background: `conic-gradient(from 0deg, transparent 0%, transparent 60%, ${color} 75%, ${color} 82%, transparent 100%)`,
          }}
        />
      </div>
      {/* Content — SpotlightCard's bg-white covers the gradient except the 2px gap */}
      <div className="relative">{children}</div>
    </div>
  );
}
