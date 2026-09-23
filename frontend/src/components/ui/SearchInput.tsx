import { useEffect, useState } from "react";

import { Input } from "./Input";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
}

export function SearchInput({ value, onChange, placeholder = "Search...", debounceMs = 300 }: SearchInputProps) {
  const [draft, setDraft] = useState(value);
  const [lastSyncedValue, setLastSyncedValue] = useState(value);

  // Adjusting state during render (not in an effect) when a prop changes:
  // keeps the input in sync if the parent resets/clears the value externally.
  if (value !== lastSyncedValue) {
    setLastSyncedValue(value);
    setDraft(value);
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (draft !== value) onChange(draft);
    }, debounceMs);
    return () => window.clearTimeout(timer);
  }, [draft, value, onChange, debounceMs]);

  return (
    <Input
      type="search"
      value={draft}
      onChange={(event) => setDraft(event.target.value)}
      placeholder={placeholder}
      aria-label={placeholder}
    />
  );
}
