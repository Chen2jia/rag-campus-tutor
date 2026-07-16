<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  askRag,
  listDocuments,
  login,
  register,
  searchDocumentChunks,
  uploadDocument,
  type DocumentChunkSearchResult,
  type DocumentRead,
  type RagAskResponse,
  type User,
} from "./api/client";

const token = ref(localStorage.getItem("edumate_token") ?? "");
const user = ref<User | null>(readStoredUser());
const authMode = ref<"login" | "register">("login");
const username = ref("");
const email = ref("");
const password = ref("");
const documents = ref<DocumentRead[]>([]);
const selectedDocumentId = ref("");
const selectedFile = ref<File | null>(null);
const searchQuery = ref("");
const searchResults = ref<DocumentChunkSearchResult[]>([]);
const question = ref("");
const ragAnswer = ref<RagAskResponse | null>(null);
const loading = ref("");
const notice = ref("");
const errorMessage = ref("");

const isAuthenticated = computed(() => Boolean(token.value && user.value));
const selectedDocument = computed(() =>
  documents.value.find((document) => document.id === selectedDocumentId.value),
);
const canSubmitAuth = computed(() => {
  if (authMode.value === "register" && username.value.trim().length < 2) {
    return false;
  }
  return email.value.trim().length > 2 && password.value.length >= 8;
});

onMounted(async () => {
  if (isAuthenticated.value) {
    await refreshDocuments();
  }
});

function readStoredUser(): User | null {
  const raw = localStorage.getItem("edumate_user");
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as User;
  } catch {
    localStorage.removeItem("edumate_user");
    return null;
  }
}

async function submitAuth() {
  if (!canSubmitAuth.value) {
    return;
  }
  await runTask("auth", async () => {
    const response =
      authMode.value === "login"
        ? await login(email.value.trim(), password.value)
        : await register(username.value.trim(), email.value.trim(), password.value);
    token.value = response.access_token;
    user.value = response.user;
    localStorage.setItem("edumate_token", response.access_token);
    localStorage.setItem("edumate_user", JSON.stringify(response.user));
    notice.value = `已进入 ${response.user.username} 的学习空间`;
    await refreshDocuments();
  });
}

function logout() {
  token.value = "";
  user.value = null;
  documents.value = [];
  selectedDocumentId.value = "";
  searchResults.value = [];
  ragAnswer.value = null;
  localStorage.removeItem("edumate_token");
  localStorage.removeItem("edumate_user");
}

async function refreshDocuments() {
  if (!token.value) {
    return;
  }
  await runTask("documents", async () => {
    documents.value = await listDocuments(token.value);
    if (
      selectedDocumentId.value &&
      !documents.value.some((document) => document.id === selectedDocumentId.value)
    ) {
      selectedDocumentId.value = "";
    }
  });
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
}

async function submitUpload() {
  if (!token.value || !selectedFile.value) {
    return;
  }
  await runTask("upload", async () => {
    await uploadDocument(token.value, selectedFile.value as File);
    selectedFile.value = null;
    notice.value = "PDF 已处理完成";
    await refreshDocuments();
  });
}

async function submitSearch() {
  if (!token.value || !searchQuery.value.trim()) {
    return;
  }
  await runTask("search", async () => {
    const response = await searchDocumentChunks(
      token.value,
      searchQuery.value.trim(),
      selectedDocumentId.value,
    );
    searchResults.value = response.results;
    notice.value = `找到 ${response.total} 个片段`;
  });
}

async function submitQuestion() {
  if (!token.value || !question.value.trim()) {
    return;
  }
  await runTask("rag", async () => {
    ragAnswer.value = await askRag(token.value, question.value.trim(), selectedDocumentId.value);
    notice.value = ragAnswer.value.is_placeholder ? "已返回检索上下文" : "已生成回答";
  });
}

async function runTask(name: string, task: () => Promise<void>) {
  loading.value = name;
  errorMessage.value = "";
  notice.value = "";
  try {
    await task();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "操作失败";
  } finally {
    loading.value = "";
  }
}
</script>

<template>
  <main class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">EduMate</p>
        <h1>学习资料工作台</h1>
      </div>
      <div v-if="isAuthenticated" class="session">
        <span>{{ user?.username }}</span>
        <button type="button" class="ghost-button" @click="logout">退出</button>
      </div>
    </header>

    <section v-if="!isAuthenticated" class="auth-panel">
      <div class="auth-tabs">
        <button
          type="button"
          :class="{ active: authMode === 'login' }"
          @click="authMode = 'login'"
        >
          登录
        </button>
        <button
          type="button"
          :class="{ active: authMode === 'register' }"
          @click="authMode = 'register'"
        >
          注册
        </button>
      </div>
      <form class="auth-form" @submit.prevent="submitAuth">
        <label v-if="authMode === 'register'">
          用户名
          <input v-model="username" autocomplete="username" minlength="2" />
        </label>
        <label>
          邮箱
          <input v-model="email" autocomplete="email" type="email" />
        </label>
        <label>
          密码
          <input v-model="password" autocomplete="current-password" type="password" minlength="8" />
        </label>
        <button type="submit" class="primary-button" :disabled="!canSubmitAuth || loading === 'auth'">
          {{ loading === "auth" ? "处理中" : authMode === "login" ? "登录" : "创建账号" }}
        </button>
      </form>
    </section>

    <section v-else class="workspace-grid">
      <aside class="document-panel">
        <div class="panel-heading">
          <h2>资料</h2>
          <button type="button" class="ghost-button" @click="refreshDocuments">刷新</button>
        </div>

        <form class="upload-row" @submit.prevent="submitUpload">
          <input type="file" accept="application/pdf" @change="handleFileChange" />
          <button type="submit" class="primary-button" :disabled="!selectedFile || loading === 'upload'">
            {{ loading === "upload" ? "处理中" : "上传" }}
          </button>
        </form>

        <label class="select-label">
          文档范围
          <select v-model="selectedDocumentId">
            <option value="">全部文档</option>
            <option v-for="document in documents" :key="document.id" :value="document.id">
              {{ document.filename }}
            </option>
          </select>
        </label>

        <div class="document-list">
          <article v-for="document in documents" :key="document.id" class="document-item">
            <div>
              <strong>{{ document.filename }}</strong>
              <p>{{ document.total_chunks }} chunks · {{ document.status }}</p>
            </div>
            <button type="button" class="small-button" @click="selectedDocumentId = document.id">
              选择
            </button>
          </article>
          <p v-if="documents.length === 0" class="empty-state">暂无资料</p>
        </div>
      </aside>

      <section class="main-panel">
        <div class="status-line" aria-live="polite">
          <span v-if="selectedDocument">当前：{{ selectedDocument.filename }}</span>
          <span v-else>当前：全部资料</span>
          <strong v-if="notice">{{ notice }}</strong>
          <strong v-if="errorMessage" class="error-text">{{ errorMessage }}</strong>
        </div>

        <div class="tool-grid">
          <section class="tool-panel">
            <h2>检索</h2>
            <form class="query-row" @submit.prevent="submitSearch">
              <input v-model="searchQuery" placeholder="输入关键词" />
              <button type="submit" class="primary-button" :disabled="!searchQuery.trim() || loading === 'search'">
                {{ loading === "search" ? "检索中" : "检索" }}
              </button>
            </form>
            <div class="result-list">
              <article v-for="result in searchResults" :key="result.id" class="result-item">
                <div class="result-meta">
                  <span>{{ result.filename }}</span>
                  <span>第 {{ result.page_start }}-{{ result.page_end }} 页</span>
                  <span v-if="result.contains_formula">含公式</span>
                </div>
                <h3>{{ result.path }}</h3>
                <p>{{ result.text }}</p>
              </article>
              <p v-if="searchResults.length === 0" class="empty-state">暂无检索结果</p>
            </div>
          </section>

          <section class="tool-panel">
            <h2>问答</h2>
            <form class="query-row" @submit.prevent="submitQuestion">
              <input v-model="question" placeholder="输入问题" />
              <button type="submit" class="primary-button" :disabled="!question.trim() || loading === 'rag'">
                {{ loading === "rag" ? "生成中" : "提问" }}
              </button>
            </form>

            <article v-if="ragAnswer" class="answer-box">
              <div class="answer-meta">
                <span>{{ ragAnswer.answer_provider }}</span>
                <span>{{ ragAnswer.is_placeholder ? "placeholder" : ragAnswer.model }}</span>
              </div>
              <p>{{ ragAnswer.answer }}</p>
              <div class="source-list">
                <span v-for="source in ragAnswer.sources" :key="`${source.document_id}-${source.chunk_index}`">
                  {{ source.filename }} · {{ source.path }} · {{ source.page_start }}-{{ source.page_end }}
                </span>
              </div>
            </article>
            <p v-else class="empty-state">暂无回答</p>
          </section>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

.app-shell {
  min-height: 100vh;
  padding: 24px;
  background: #f4f6f8;
  color: #172033;
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  max-width: 1240px;
  margin: 0 auto 20px;
}

.eyebrow {
  margin: 0 0 4px;
  color: #3563e9;
  font-size: 13px;
  font-weight: 700;
}

h1,
h2,
h3,
p {
  margin: 0;
}

h1 {
  font-size: 30px;
  line-height: 1.2;
}

h2 {
  font-size: 18px;
}

h3 {
  font-size: 15px;
}

button,
input,
select {
  font: inherit;
}

button {
  border: 0;
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

input,
select {
  width: 100%;
  min-height: 42px;
  border: 1px solid #d5dbe5;
  border-radius: 6px;
  padding: 0 12px;
  background: #ffffff;
  color: #172033;
}

.primary-button,
.ghost-button,
.small-button {
  min-height: 38px;
  border-radius: 6px;
  padding: 0 14px;
  white-space: nowrap;
}

.primary-button {
  background: #2454d6;
  color: #ffffff;
  font-weight: 700;
}

.ghost-button,
.small-button {
  background: #e7ebf2;
  color: #23314a;
}

.session,
.panel-heading,
.query-row,
.upload-row,
.status-line,
.answer-meta,
.result-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.session {
  justify-content: flex-end;
}

.auth-panel,
.workspace-grid {
  max-width: 1240px;
  margin: 0 auto;
}

.auth-panel {
  width: min(440px, 100%);
  padding: 20px;
  border: 1px solid #dfe4ec;
  border-radius: 8px;
  background: #ffffff;
}

.auth-tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.auth-tabs button {
  min-height: 40px;
  border-radius: 6px;
  background: #eef2f7;
  color: #536070;
}

.auth-tabs button.active {
  background: #172033;
  color: #ffffff;
}

.auth-form {
  display: grid;
  gap: 14px;
}

label,
.select-label {
  display: grid;
  gap: 6px;
  color: #536070;
  font-size: 13px;
  font-weight: 700;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 18px;
}

.document-panel,
.tool-panel {
  border: 1px solid #dfe4ec;
  border-radius: 8px;
  background: #ffffff;
}

.document-panel {
  display: grid;
  align-content: start;
  gap: 16px;
  padding: 16px;
}

.panel-heading {
  justify-content: space-between;
}

.upload-row,
.query-row {
  align-items: stretch;
}

.upload-row input {
  padding-top: 8px;
}

.document-list,
.result-list {
  display: grid;
  gap: 10px;
}

.document-item,
.result-item,
.answer-box {
  border: 1px solid #e3e8ef;
  border-radius: 8px;
  padding: 12px;
  background: #fbfcfe;
}

.document-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.document-item strong,
.result-item h3 {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-item p,
.empty-state,
.result-item p,
.answer-box p {
  color: #536070;
  line-height: 1.55;
}

.main-panel {
  display: grid;
  gap: 14px;
}

.status-line {
  justify-content: space-between;
  min-height: 42px;
  border: 1px solid #dfe4ec;
  border-radius: 8px;
  padding: 0 14px;
  background: #ffffff;
  color: #536070;
}

.status-line strong {
  color: #12715b;
}

.status-line .error-text {
  color: #b42318;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.tool-panel {
  display: grid;
  align-content: start;
  gap: 14px;
  padding: 16px;
}

.result-meta,
.answer-meta {
  flex-wrap: wrap;
  color: #647084;
  font-size: 12px;
}

.result-meta span,
.answer-meta span,
.source-list span {
  border-radius: 999px;
  padding: 4px 8px;
  background: #edf1f6;
}

.result-item {
  display: grid;
  gap: 8px;
}

.result-item p,
.answer-box p {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 5;
}

.answer-box {
  display: grid;
  gap: 12px;
}

.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: #536070;
  font-size: 12px;
}

@media (max-width: 920px) {
  .workspace-grid,
  .tool-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .app-shell {
    padding: 16px;
  }

  .topbar,
  .status-line,
  .query-row,
  .upload-row {
    align-items: stretch;
    flex-direction: column;
  }

  h1 {
    font-size: 24px;
  }
}
</style>
