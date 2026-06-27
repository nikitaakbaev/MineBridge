export function isNetworkFetchError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  return /failed to fetch|networkerror when attempting to fetch resource/i.test(error.message);
}
