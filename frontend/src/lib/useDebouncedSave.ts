import { useEffect, useRef } from "react";

/**
 * Calls ``save`` ``delayMs`` after ``value`` last changed.
 *
 * The first render is skipped so we don't write the freshly-loaded server value
 * straight back. ``equals`` compares previous vs. current value to detect real
 * changes (objects equal by JSON serialization by default).
 */
export function useDebouncedSave<T>(
  value: T,
  save: (value: T) => void,
  delayMs = 350,
  equals: (a: T, b: T) => boolean = (a, b) => JSON.stringify(a) === JSON.stringify(b)
): void {
  const previousRef = useRef<T | null>(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
      previousRef.current = value;
      return;
    }
    if (previousRef.current !== null && equals(previousRef.current, value)) return;
    previousRef.current = value;
    const timer = window.setTimeout(() => save(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, save, delayMs, equals]);
}
