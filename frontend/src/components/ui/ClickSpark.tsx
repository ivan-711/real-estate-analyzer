import { useRef, useState } from "react";
import { motion } from "motion/react";

interface Spark {
  id: number;
  x: number;
  y: number;
  angle: number;
}

interface ClickSparkProps {
  children: React.ReactNode;
  sparkColor?: string;
  sparkSize?: number;
  sparkCount?: number;
  className?: string;
}

export default function ClickSpark({
  children,
  sparkColor = "#2563EB",
  sparkSize = 6,
  sparkCount = 8,
  className = "relative inline-flex",
}: ClickSparkProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [sparks, setSparks] = useState<Spark[]>([]);
  const nextId = useRef(0);

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const newSparks: Spark[] = Array.from({ length: sparkCount }, (_, i) => ({
      id: nextId.current++,
      x,
      y,
      angle: i * (360 / sparkCount),
    }));
    setSparks((prev) => [...prev, ...newSparks]);
  };

  const removeSpark = (id: number) => {
    setSparks((prev) => prev.filter((s) => s.id !== id));
  };

  return (
    <div ref={containerRef} className={className} onClick={handleClick}>
      {children}
      {sparks.map((spark) => {
        const rad = (spark.angle * Math.PI) / 180;
        return (
          <motion.span
            key={spark.id}
            className="pointer-events-none absolute rounded-full"
            style={{
              width: sparkSize,
              height: sparkSize,
              backgroundColor: sparkColor,
              left: spark.x - sparkSize / 2,
              top: spark.y - sparkSize / 2,
            }}
            initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
            animate={{
              x: Math.cos(rad) * 30,
              y: Math.sin(rad) * 30,
              opacity: 0,
              scale: 0,
            }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            onAnimationComplete={() => removeSpark(spark.id)}
          />
        );
      })}
    </div>
  );
}
