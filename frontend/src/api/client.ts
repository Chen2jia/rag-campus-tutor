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

export type TaskRead = {
  id: string;
  title: string;
  subject: string | null;
  priority: number;
  due_date: string | null;
  is_done: boolean;
  created_at: string;
};

export type TaskPayload = {
  title: string;
  subject?: string | null;
  priority?: number;
  due_date?: string | null;
};

export type ReviewRead = {
  id: string;
  knowledge_point: string;
  subject: string | null;
  interval_days: number;
  next_review_date: string;
  ease_factor: number;
  created_at: string;
};

export type ReviewRateResponse = {
  item: ReviewRead;
  score: number;
  next_interval_days: number;
  next_review_date: string;
};

export type PlanDay = {
  day: number;
  date: string;
  title: string;
  description: string;
};

export type PlanGenerateResponse = {
  plan_text: string;
  days: PlanDay[];
  created_tasks: TaskRead[];
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

export function listTasks(token: string): Promise<TaskRead[]> {
  return request<TaskRead[]>("/tasks", { token });
}

export function createTask(token: string, payload: TaskPayload): Promise<TaskRead> {
  return request<TaskRead>("/tasks", {
    token,
    method: "POST",
    body: payload,
  });
}

export function updateTask(
  token: string,
  taskId: string,
  payload: Partial<TaskPayload> & { is_done?: boolean },
): Promise<TaskRead> {
  return request<TaskRead>(`/tasks/${taskId}`, {
    token,
    method: "PUT",
    body: payload,
  });
}

export function deleteTask(token: string, taskId: string): Promise<unknown> {
  return request<unknown>(`/tasks/${taskId}`, {
    token,
    method: "DELETE",
  });
}

export function listTodayReviews(token: string): Promise<ReviewRead[]> {
  return request<ReviewRead[]>("/review/today", { token });
}

export function createReview(
  token: string,
  knowledgePoint: string,
  subject: string,
  nextReviewDate: string,
): Promise<ReviewRead> {
  return request<ReviewRead>("/review", {
    token,
    method: "POST",
    body: {
      knowledge_point: knowledgePoint,
      subject: subject || null,
      next_review_date: nextReviewDate || null,
    },
  });
}

export function rateReview(token: string, reviewId: string, score: number): Promise<ReviewRateResponse> {
  return request<ReviewRateResponse>(`/review/${reviewId}/rate`, {
    token,
    method: "PUT",
    body: { score },
  });
}

export function generatePlan(
  token: string,
  goal: string,
  days: number,
  subject: string,
  startDate: string,
): Promise<PlanGenerateResponse> {
  return request<PlanGenerateResponse>("/plan/generate", {
    token,
    method: "POST",
    body: {
      goal,
      days,
      subject: subject || null,
      start_date: startDate || null,
    },
  });
}
