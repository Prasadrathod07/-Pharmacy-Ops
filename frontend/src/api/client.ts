export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string | null;
  };
}

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;
  requestId: string | null;

  constructor(status: number, body: ApiErrorBody) {
    super(body.error.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.error.code;
    this.details = body.error.details ?? {};
    this.requestId = body.error.request_id ?? null;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let parsed: ApiErrorBody;
    try {
      parsed = await response.json();
    } catch {
      parsed = {
        error: {
          code: "UNKNOWN_ERROR",
          message: `Request failed with status ${response.status}`,
        },
      };
    }
    throw new ApiError(response.status, parsed);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
