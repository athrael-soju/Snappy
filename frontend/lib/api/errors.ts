type ErrorLike = {
  message?: unknown;
  status?: unknown;
  response?: {
    status?: unknown;
    data?: {
      detail?: unknown;
      message?: unknown;
      error?: unknown;
    };
  };
};

/**
 * Derive a user-facing error message from an unknown error value.
 */
export function getErrorMessage(error: unknown, fallback: string): string {
  if (!error) {
    return fallback;
  }

  if (typeof error === "string") {
    return error;
  }

  if (error instanceof Error) {
    const status = (error as ErrorLike).response?.status ?? (error as ErrorLike).status;
    return status ? `${status}: ${error.message}` : error.message || fallback;
  }

  if (typeof error === "object") {
    const err = error as ErrorLike;
    const status = err.response?.status ?? err.status;
    const detail =
      typeof err.response?.data?.message === "string"
        ? err.response?.data?.message
        : typeof err.response?.data?.detail === "string"
        ? err.response?.data?.detail
        : typeof err.response?.data?.error === "string"
        ? err.response?.data?.error
        : undefined;
    const message =
      typeof err.message === "string"
        ? err.message
        : detail ?? fallback;
    return status ? `${status}: ${message}` : message;
  }

  return fallback;
}
