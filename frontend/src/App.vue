<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  listDocuments,
  listTasks,
  listTodayReviews,
  login,
  register,
  type DocumentRead,
  type PlanGenerateResponse,
  type ReviewRead,
  type TaskRead,
  type User,
} from "./api/client";
import ChatPanel from "./components/ChatPanel.vue";
import DocumentLibraryPanel from "./components/DocumentLibraryPanel.vue";
import PlanPanel from "./components/PlanPanel.vue";
import ReviewPanel from "./components/ReviewPanel.vue";
import TaskPanel from "./components/TaskPanel.vue";

type WorkspaceTab = "chat" | "library" | "tasks" | "review" | "plan";

const token = ref(localStorage.getItem("edumate_token") ?? "");
const user = ref<User | null>(readStoredUser());
const activeTab = ref<WorkspaceTab>("chat");
const authMode = ref<"login" | "register">("login");
const username = ref("");
const email = ref("");
const password = ref("");
const documents = ref<DocumentRead[]>([]);
const selectedDocumentId = ref("");
const tasks = ref<TaskRead[]>([]);
const reviews = ref<ReviewRead[]>([]);
const planResult = ref<PlanGenerateResponse | null>(null);
const loading = ref("");
const notice = ref("");
const errorMessage = ref("");

const isAuthenticated = computed(() => Boolean(token.value && user.value));
const selectedDocument = computed(() =>
  documents.value.find((document) => document.id === selectedDocumentId.value),
);
const openTasks = computed(() => tasks.value.filter((task) => !task.is_done));
const canSubmitAuth = computed(() => {
  if (authMode.value === "register" && username.value.trim().length < 2) {
    return false;
  }
  return email.value.trim().length > 2 && password.value.length >= 8;
});

const tabs = computed<Array<{ id: WorkspaceTab; label: string; count: number | null }>>(() => [
  { id: "chat", label: "聊天", count: null },
  { id: "library", label: "资料问答", count: documents.value.length },
  { id: "tasks", label: "任务", count: openTasks.value.length },
  { id: "review", label: "复习", count: reviews.value.length },
  { id: "plan", label: "计划", count: planResult.value?.days.length ?? null },
]);

onMounted(async () => {
  if (isAuthenticated.value) {
    await refreshWorkspace();
  }
});

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

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
    await loadWorkspaceData();
    notice.value = `已进入 ${response.user.username} 的学习空间`;
  });
}

function logout() {
  token.value = "";
  user.value = null;
  documents.value = [];
  selectedDocumentId.value = "";
  tasks.value = [];
  reviews.value = [];
  planResult.value = null;
  localStorage.removeItem("edumate_token");
  localStorage.removeItem("edumate_user");
}

async function refreshWorkspace() {
  if (!token.value) {
    return;
  }
  await loadWorkspaceData();
  notice.value = "工作台已刷新";
}

async function loadWorkspaceData() {
  const [nextDocuments, nextTasks, nextReviews] = await Promise.all([
    listDocuments(token.value),
    listTasks(token.value),
    listTodayReviews(token.value),
  ]);
  documents.value = nextDocuments;
  tasks.value = nextTasks;
  reviews.value = nextReviews;
  if (
    selectedDocumentId.value &&
    !documents.value.some((document) => document.id === selectedDocumentId.value)
  ) {
    selectedDocumentId.value = "";
  }
}

function updateLibraryDocuments(nextDocuments: DocumentRead[]) {
  documents.value = nextDocuments;
}

function updateSelectedDocumentId(nextDocumentId: string) {
  selectedDocumentId.value = nextDocumentId;
}

function updateTasks(nextTasks: TaskRead[]) {
  tasks.value = nextTasks;
}

function updateReviews(nextReviews: ReviewRead[]) {
  reviews.value = nextReviews;
}

function updatePlanResult(nextPlanResult: PlanGenerateResponse | null) {
  planResult.value = nextPlanResult;
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
        <h1>校园学习助手</h1>
      </div>
      <div v-if="isAuthenticated" class="session">
        <span>{{ user?.username }}</span>
        <button type="button" class="ghost-button" @click="refreshWorkspace">刷新</button>
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
      <p v-if="errorMessage" class="auth-error">{{ errorMessage }}</p>
    </section>

    <section v-else class="workspace">
      <nav class="workspace-tabs" aria-label="工作区">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
          <span v-if="tab.count !== null" class="tab-count">{{ tab.count }}</span>
        </button>
      </nav>

      <div class="status-line" aria-live="polite">
        <span v-if="selectedDocument">当前资料：{{ selectedDocument.filename }}</span>
        <span v-else>当前资料：全部</span>
        <strong v-if="notice">{{ notice }}</strong>
        <strong v-if="errorMessage" class="error-text">{{ errorMessage }}</strong>
      </div>

      <section v-show="activeTab === 'chat'" class="chat-section">
        <ChatPanel
          :token="token"
          :selected-document-id="selectedDocumentId"
          :selected-document-name="selectedDocument?.filename ?? ''"
        />
      </section>

      <DocumentLibraryPanel
        v-show="activeTab === 'library'"
        :token="token"
        :documents="documents"
        :selected-document-id="selectedDocumentId"
        @update:documents="updateLibraryDocuments"
        @update:selected-document-id="updateSelectedDocumentId"
        @notice="notice = $event"
        @error="errorMessage = $event"
      />

      <TaskPanel
        v-show="activeTab === 'tasks'"
        :token="token"
        :tasks="tasks"
        @update:tasks="updateTasks"
        @notice="notice = $event"
        @error="errorMessage = $event"
      />

      <ReviewPanel
        v-show="activeTab === 'review'"
        :token="token"
        :reviews="reviews"
        @update:reviews="updateReviews"
        @notice="notice = $event"
        @error="errorMessage = $event"
      />

      <PlanPanel
        v-show="activeTab === 'plan'"
        :token="token"
        :plan-result="planResult"
        @update:plan-result="updatePlanResult"
        @update:tasks="updateTasks"
        @notice="notice = $event"
        @error="errorMessage = $event"
      />
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

.topbar,
.workspace,
.auth-panel {
  max-width: 1240px;
  margin: 0 auto;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.eyebrow {
  margin: 0 0 4px;
  color: #2454d6;
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
.small-button,
.score-button {
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
.small-button,
.score-button {
  background: #e7ebf2;
  color: #23314a;
}

.session,
.panel-heading,
.query-row,
.upload-row,
.status-line,
.answer-meta,
.result-meta,
.score-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.session {
  justify-content: flex-end;
}

.auth-panel {
  width: min(440px, 100%);
  padding: 20px;
  border: 1px solid #dfe4ec;
  border-radius: 8px;
  background: #ffffff;
}

.auth-tabs,
.workspace-tabs {
  display: grid;
  gap: 8px;
}

.auth-tabs {
  grid-template-columns: repeat(2, 1fr);
  margin-bottom: 16px;
}

.workspace-tabs {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 12px;
}

.auth-tabs button,
.workspace-tabs button {
  min-height: 40px;
  border-radius: 6px;
  background: #eef2f7;
  color: #536070;
}

.auth-tabs button.active,
.workspace-tabs button.active {
  background: #172033;
  color: #ffffff;
}

.tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  min-height: 22px;
  margin-left: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 12px;
}

.auth-form,
.form-grid,
.document-panel,
.tool-panel,
.panel,
.workspace {
  display: grid;
  gap: 14px;
}

.auth-error,
.error-text {
  color: #b42318;
}

.field {
  display: grid;
  gap: 6px;
  color: #536070;
  font-size: 13px;
  font-weight: 700;
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

.library-grid,
.two-column {
  display: grid;
  gap: 18px;
}

.library-grid {
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
}

.two-column,
.tool-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.panel,
.document-panel,
.tool-panel {
  align-content: start;
  border: 1px solid #dfe4ec;
  border-radius: 8px;
  padding: 16px;
  background: #ffffff;
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
.result-list,
.item-list,
.plan-result {
  display: grid;
  gap: 10px;
}

.document-item,
.result-item,
.answer-box,
.task-item,
.review-item,
.plan-day {
  border: 1px solid #e3e8ef;
  border-radius: 8px;
  padding: 12px;
  background: #fbfcfe;
}

.document-item,
.task-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.task-item {
  grid-template-columns: auto minmax(0, 1fr) auto;
}

.task-item.done strong {
  color: #7a8596;
  text-decoration: line-through;
}

.review-item,
.plan-day,
.result-item,
.answer-box {
  display: grid;
  gap: 8px;
}

.document-item strong,
.result-item h3,
.task-item strong,
.review-item strong,
.plan-day strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-item p,
.empty-state,
.result-item p,
.answer-box p,
.task-item p,
.review-item p,
.plan-result p,
.plan-day p {
  color: #536070;
  line-height: 1.55;
}

.result-meta,
.answer-meta {
  flex-wrap: wrap;
  color: #647084;
  font-size: 12px;
}

.result-meta span,
.answer-meta span,
.source-list span,
.counter,
.plan-day span {
  border-radius: 999px;
  padding: 4px 8px;
  background: #edf1f6;
  color: #536070;
  font-size: 12px;
}

.result-item p,
.answer-box p {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 5;
}

.source-list,
.score-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.score-button {
  min-width: 38px;
  padding: 0;
}

.split-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 980px) {
  .library-grid,
  .two-column,
  .tool-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .app-shell {
    padding: 16px;
  }

  .topbar,
  .status-line,
  .query-row,
  .upload-row,
  .session {
    align-items: stretch;
    flex-direction: column;
  }

  .workspace-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .split-row {
    grid-template-columns: 1fr;
  }

  h1 {
    font-size: 24px;
  }
}
</style>
