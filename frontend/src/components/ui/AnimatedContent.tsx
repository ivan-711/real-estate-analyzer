import { motion } from "motion/react";

interface AnimatedContentProps {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}

/**
 * Fades + slides content in on mount using opacity + translateY only.
 * NEVER animates height or scale — safe to wrap Recharts ResponsiveContainer.
 */
export default function AnimatedContent({
  children,
  delay = 0,
  className,
}: AnimatedContentProps) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut", delay: delay / 1000 }}
    >
      {children}
    </motion.div>
  );
}
