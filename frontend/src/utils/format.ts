export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDurationSince(isoString: string): string {
  const since = new Date(isoString).getTime();
  if (Number.isNaN(since)) return "—";
  const minutes = Math.max(0, (Date.now() - since) / 60000);
  return formatMinutes(minutes);
}

export function formatMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (value < 60) return `${Math.round(value)} min`;
  const hours = Math.floor(value / 60);
  const minutes = Math.round(value % 60);
  return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
}
