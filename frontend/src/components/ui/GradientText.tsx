interface GradientTextProps {
  children: React.ReactNode;
  /** Two or more CSS color values for the gradient. */
  colors?: string[];
  /** Animation cycle duration in seconds. Default: 8. */
  animationSpeed?: number;
  className?: string;
}

/**
 * Renders text with an animated sliding gradient.
 * Uses background-clip: text + color: transparent so the gradient shows through.
 * Works alongside Tailwind text-* classes — inline styles take precedence.
 */
export default function GradientText({
  children,
  colors = ["#7c3aed", "#db2777"],
  animationSpeed = 8,
  className = "",
}: GradientTextProps) {
  // Build a seamless looping gradient by repeating the first color at the end
  const stops = [...colors, colors[0]].join(", ");

  const style: React.CSSProperties = {
    backgroundImage: `linear-gradient(to right, ${stops})`,
    backgroundSize: "200% auto",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    WebkitTextFillColor: "transparent",
    color: "transparent",
    display: "inline-block",
    animation: `gradientTextSlide ${animationSpeed}s linear infinite`,
  };

  return (
    <>
      <style>{`
        @keyframes gradientTextSlide {
          0%   { background-position: 0% center; }
          100% { background-position: 200% center; }
        }
      `}</style>
      <span className={className} style={style}>
        {children}
      </span>
    </>
  );
}
