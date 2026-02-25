import React, { isValidElement, useEffect, useRef } from "react";
import { motion } from "motion/react";

interface AnimatedListProps {
  children: React.ReactNode;
  className?: string;
  /** Milliseconds between each new item's entrance animation. Default: 60ms. */
  staggerDelay?: number;
}

/**
 * Drop-in replacement for <ul>. Expects <li> elements as direct children.
 * New items animate in with opacity + translateY. Already-seen items stay still.
 *
 * Tracking strategy:
 * - seenKeys ref: persists which keys have already been animated
 * - batchRef: collects new keys from the current render, committed to seenKeys
 *   in useEffect (after commit) — avoids mutating seenKeys during render
 *   and works correctly under React Strict Mode double-invocation
 */
export default function AnimatedList({
  children,
  className,
  staggerDelay = 60,
}: AnimatedListProps) {
  const seenKeys = useRef<Set<string>>(new Set());
  const batchRef = useRef<string[]>([]);

  const childArray = React.Children.toArray(children);

  // Collect new keys this render (without mutating seenKeys yet)
  const batchThisRender: string[] = [];
  let newCount = 0;

  const items = childArray.map((child, index) => {
    if (!isValidElement(child)) return child;

    // React.Children.toArray prefixes keys with ".$" — use as-is for stable tracking
    const key = String(child.key ?? index);
    const isNew = !seenKeys.current.has(key);

    if (isNew) {
      batchThisRender.push(key);
    }

    // stagger only within the new batch; cap total stagger at 500ms
    const delay = isNew ? Math.min(newCount++ * staggerDelay, 500) / 1000 : 0;

    // Extract the <li>'s className and children so we can render motion.li
    const element = child as React.ReactElement<{
      className?: string;
      children?: React.ReactNode;
    }>;

    return (
      <motion.li
        key={key}
        className={element.props.className}
        initial={isNew ? { opacity: 0, y: 8 } : false}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: "easeOut", delay }}
      >
        {element.props.children}
      </motion.li>
    );
  });

  // Persist this render's new keys AFTER commit (avoids Strict Mode double-run issues)
  batchRef.current = batchThisRender;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    batchRef.current.forEach((k) => seenKeys.current.add(k));
  });

  return <ul className={className}>{items}</ul>;
}
