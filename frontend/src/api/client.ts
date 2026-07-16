const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export type User = {
  id: string;
  username: string;
  email: string;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type DocumentRead = {
  id: string;
  filename: string;
  total_chunks: number;
  status: string;
  error_message: string | null;
  created_at: string;
};

export type DocumentChunkSearchResult = {
  id: string;
  document_id: string;
  filename: string;
  chunk_index: number;
  path: string;
  section: string;
  text: string;
  page_start: number;
  page_end: number;
  contains_formula: boolean;
  formulas_metadata: Array<Record<string, unknown>>;
};

export type DocumentChunkSearchResponse = {
  query: string;
  total: number;
  results: DocumentChunkSearchResult[];
};

export type RagSource = {
  document_id: string;
  filename: string;
  chunk_index: number;
  path: string;
  page_start: number;
  page_end: number;
  contains_formula: boolean;
};

export type RagAskResponse = {
  question: string;
  answer: string;
  sources: RagSource[];
  context_text: string;
  is_placeholder: boolean;
  answer_provider: string;
  model: string | null;
};

type RequestOptions = {
  token?: string;
  method?: string;
  body?: BodyInit | object;
  headers?: HeadersInit;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body;
  } else if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body,
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }

  return (await response.json()) as T;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    return `Request failed with ${response.status}`;
  }
  return `Request failed with ${response.status}`;
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

export function register(username: string, email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/register", {
    method: "POST",
    body: { username, email, password },
  });
}

export function listDocuments(token: string): Promise<DocumentRead[]> {
  return request<DocumentRead[]>("/documents", { token });
}

export function uploadDocument(token: string, file: File): Promise<unknown> {
  const formData = new FormData();
  formData.append("file", file);
  return request<unknown>("/documents/upload", {
    token,
    method: "POST",
    body: formData,
  });
}

export function searchDocumentChunks(
  token: string,
  query: string,
  documentId: string,
): Promise<DocumentChunkSearchResponse> {
  const params = new URLSearchParams({ q: query, limit: "8" });
  if (documentId) {
    params.set("document_id", documentId);
  }
  return request<DocumentChunkSearchResponse>(`/documents/chunks/search?${params.toString()}`, {
    token,
  });
}

export function askRag(token: string, question: string, documentId: string): Promise<RagAskResponse> {
  return request<RagAskResponse>("/rag/ask", {
    token,
    method: "POST",
    body: {
      question,
      limit: 5,
      document_id: documentId || null,
    },
  });
}
