<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  listDocuments,
  listTasks,
  listTodayReviews,
  type DocumentRead,
  type PlanGenerateResponse,
  type ReviewRead,
  type TaskRead,
  type TokenResponse,
  type User,
} from "./api/client";
import AuthPanel from "./components/AuthPanel.vue";
import ChatPanel from "./components/ChatPanel.vue";
import DocumentLibraryPanel from "./components/DocumentLibraryPanel.vue";
import PlanPanel from "./components/PlanPanel.vue";
import ReviewPanel from "./components/ReviewPanel.vue";
import TaskPanel from "./components/TaskPanel.vue";

type WorkspaceTab = "chat" | "library" | "tasks" | "review" | "plan";

const token = ref(localStorage.getItem("edumate_token") ?? "");
const user = ref<User | null>(readStoredUser());
const activeTab = ref<WorkspaceTab>("chat");
const documents = ref<DocumentRead[]>([]);
const selectedDocumentId = ref("");
const tasks = ref<TaskRead[]>([]);
const reviews = ref<ReviewRead[]>([]);
const planResult = ref<PlanGenerateResponse | null>(null);
const notice = ref("");
const errorMessage = ref("");

const isAuthenticated = computed(() => Boolean(token.value && user.value));
const selectedDocument = computed(() =>
  documents.value.find((document) => document.id === selectedDocumentId.value),
);
const openTasks = computed(() => tasks.value.filter((task) => !task.is_done));

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

async function handleAuthenticated(response: TokenResponse) {
  token.value = response.access_token;
  user.value = response.user;
  localStorage.setItem("edumate_token", response.access_token);
  localStorage.setItem("edumate_user", JSON.stringify(response.user));
  errorMessage.value = "";
  await loadWorkspaceData();
  notice.value = `已进入 ${response.user.username} 的学习空间`;
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

    <AuthPanel v-if="!isAuthenticated" @authenticated="handleAuthenticated" />
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
.workspace {
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

.eyebrow,
h1,
p {
  margin: 0;
}

.eyebrow {
  margin-bottom: 4px;
  color: #2454d6;
  font-size: 13px;
  font-weight: 700;
}

h1 {
  font-size: 30px;
  line-height: 1.2;
}

button {
  border: 0;
  cursor: pointer;
  font: inherit;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.ghost-button {
  min-height: 38px;
  border-radius: 6px;
  padding: 0 14px;
  background: #e7ebf2;
  color: #23314a;
  white-space: nowrap;
}

.session,
.status-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

.session {
  justify-content: flex-end;
}

.workspace {
  display: grid;
  gap: 14px;
}

.workspace-tabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.workspace-tabs button {
  min-height: 40px;
  border-radius: 6px;
  background: #eef2f7;
  color: #536070;
}

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

@media (max-width: 680px) {
  .app-shell {
    padding: 16px;
  }

  .topbar,
  .status-line,
  .session {
    align-items: stretch;
    flex-direction: column;
  }

  .workspace-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  h1 {
    font-size: 24px;
  }
}
</style>
