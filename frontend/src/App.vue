<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import {
  askRag,
  createReview,
  createTask,
  deleteTask,
  generatePlan,
  listDocuments,
  listTasks,
  listTodayReviews,
  login,
  rateReview,
  register,
  searchDocumentChunks,
  updateTask,
  uploadDocument,
  type DocumentChunkSearchResult,
  type DocumentRead,
  type PlanGenerateResponse,
  type RagAskResponse,
  type ReviewRead,
  type TaskRead,
  type User,
} from "./api/client";
import ChatPanel from "./components/ChatPanel.vue";

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
const selectedFile = ref<File | null>(null);
const searchQuery = ref("");
const searchResults = ref<DocumentChunkSearchResult[]>([]);
const question = ref("");
const ragAnswer = ref<RagAskResponse | null>(null);
const tasks = ref<TaskRead[]>([]);
const taskTitle = ref("");
const taskSubject = ref("");
const taskPriority = ref(3);
const taskDueDate = ref("");
const reviews = ref<ReviewRead[]>([]);
const reviewPoint = ref("");
const reviewSubject = ref("");
const reviewDate = ref(today());
const planGoal = ref("");
const planDays = ref(7);
const planSubject = ref("");
const planStartDate = ref(today());
const planResult = ref<PlanGenerateResponse | null>(null);
const loading = ref("");
const notice = ref("");
const errorMessage = ref("");

const isAuthenticated = computed(() => Boolean(token.value && user.value));
const selectedDocument = computed(() =>
  documents.value.find((document) => document.id === selectedDocumentId.value),
);
const openTasks = computed(() => tasks.value.filter((task) => !task.is_done));
const doneTasks = computed(() => tasks.value.filter((task) => task.is_done));
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
  searchResults.value = [];
  ragAnswer.value = null;
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

async function refreshDocuments() {
  if (!token.value) {
    return;
  }
  await loadDocumentsData();
  notice.value = "资料已刷新";
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

async function loadDocumentsData() {
  documents.value = await listDocuments(token.value);
  if (
    selectedDocumentId.value &&
    !documents.value.some((document) => document.id === selectedDocumentId.value)
  ) {
    selectedDocumentId.value = "";
  }
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
    await loadDocumentsData();
    notice.value = "PDF 已处理完成";
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

async function submitTask() {
  if (!token.value || !taskTitle.value.trim()) {
    return;
  }
  await runTask("task-create", async () => {
    await createTask(token.value, {
      title: taskTitle.value.trim(),
      subject: taskSubject.value.trim() || null,
      priority: taskPriority.value,
      due_date: taskDueDate.value || null,
    });
    taskTitle.value = "";
    taskSubject.value = "";
    taskPriority.value = 3;
    taskDueDate.value = "";
    tasks.value = await listTasks(token.value);
    notice.value = "任务已创建";
  });
}

async function toggleTask(task: TaskRead) {
  if (!token.value) {
    return;
  }
  await runTask(`task-${task.id}`, async () => {
    const updated = await updateTask(token.value, task.id, { is_done: !task.is_done });
    tasks.value = tasks.value.map((item) => (item.id === updated.id ? updated : item));
  });
}

async function removeTask(task: TaskRead) {
  if (!token.value) {
    return;
  }
  await runTask(`delete-${task.id}`, async () => {
    await deleteTask(token.value, task.id);
    tasks.value = tasks.value.filter((item) => item.id !== task.id);
    notice.value = "任务已删除";
  });
}

async function submitReview() {
  if (!token.value || !reviewPoint.value.trim()) {
    return;
  }
  await runTask("review-create", async () => {
    await createReview(
      token.value,
      reviewPoint.value.trim(),
      reviewSubject.value.trim(),
      reviewDate.value,
    );
    reviewPoint.value = "";
    reviewSubject.value = "";
    reviewDate.value = today();
    reviews.value = await listTodayReviews(token.value);
    notice.value = "复习项已创建";
  });
}

async function submitReviewScore(item: ReviewRead, score: number) {
  if (!token.value) {
    return;
  }
  await runTask(`review-${item.id}-${score}`, async () => {
    await rateReview(token.value, item.id, score);
    reviews.value = await listTodayReviews(token.value);
    notice.value = "复习进度已更新";
  });
}

async function submitPlan() {
  if (!token.value || !planGoal.value.trim()) {
    return;
  }
  await runTask("plan", async () => {
    planResult.value = await generatePlan(
      token.value,
      planGoal.value.trim(),
      planDays.value,
      planSubject.value.trim(),
      planStartDate.value,
    );
    tasks.value = await listTasks(token.value);
    notice.value = `已生成 ${planResult.value.days.length} 天计划`;
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

      <section v-show="activeTab === 'library'" class="library-grid">
        <aside class="panel document-panel">
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

          <label class="field">
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
          <div class="tool-grid">
            <section class="panel tool-panel">
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

            <section class="panel tool-panel">
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

      <section v-show="activeTab === 'tasks'" class="two-column">
        <section class="panel">
          <h2>新建任务</h2>
          <form class="form-grid" @submit.prevent="submitTask">
            <label class="field">
              标题
              <input v-model="taskTitle" placeholder="例如：完成高数第三章习题" />
            </label>
            <label class="field">
              科目
              <input v-model="taskSubject" placeholder="可选" />
            </label>
            <div class="split-row">
              <label class="field">
                优先级
                <select v-model.number="taskPriority">
                  <option v-for="priority in [1, 2, 3, 4, 5]" :key="priority" :value="priority">
                    {{ priority }}
                  </option>
                </select>
              </label>
              <label class="field">
                截止日期
                <input v-model="taskDueDate" type="date" />
              </label>
            </div>
            <button type="submit" class="primary-button" :disabled="!taskTitle.trim() || loading === 'task-create'">
              创建任务
            </button>
          </form>
        </section>

        <section class="panel">
          <div class="panel-heading">
            <h2>任务列表</h2>
            <span class="counter">{{ openTasks.length }} 未完成</span>
          </div>
          <div class="item-list">
            <article v-for="task in openTasks" :key="task.id" class="task-item">
              <input type="checkbox" :checked="task.is_done" @change="toggleTask(task)" />
              <div>
                <strong>{{ task.title }}</strong>
                <p>{{ task.subject || "未分类" }} · P{{ task.priority }} · {{ task.due_date || "无截止" }}</p>
              </div>
              <button type="button" class="small-button" @click="removeTask(task)">删除</button>
            </article>
            <article v-for="task in doneTasks" :key="task.id" class="task-item done">
              <input type="checkbox" :checked="task.is_done" @change="toggleTask(task)" />
              <div>
                <strong>{{ task.title }}</strong>
                <p>{{ task.subject || "未分类" }} · 已完成</p>
              </div>
              <button type="button" class="small-button" @click="removeTask(task)">删除</button>
            </article>
            <p v-if="tasks.length === 0" class="empty-state">暂无任务</p>
          </div>
        </section>
      </section>

      <section v-show="activeTab === 'review'" class="two-column">
        <section class="panel">
          <h2>新建复习项</h2>
          <form class="form-grid" @submit.prevent="submitReview">
            <label class="field">
              知识点
              <input v-model="reviewPoint" placeholder="例如：泰勒公式" />
            </label>
            <label class="field">
              科目
              <input v-model="reviewSubject" placeholder="可选" />
            </label>
            <label class="field">
              下次复习
              <input v-model="reviewDate" type="date" />
            </label>
            <button type="submit" class="primary-button" :disabled="!reviewPoint.trim() || loading === 'review-create'">
              创建复习项
            </button>
          </form>
        </section>

        <section class="panel">
          <div class="panel-heading">
            <h2>今日复习</h2>
            <span class="counter">{{ reviews.length }} 项</span>
          </div>
          <div class="item-list">
            <article v-for="item in reviews" :key="item.id" class="review-item">
              <div>
                <strong>{{ item.knowledge_point }}</strong>
                <p>{{ item.subject || "未分类" }} · 间隔 {{ item.interval_days }} 天 · EF {{ item.ease_factor.toFixed(2) }}</p>
              </div>
              <div class="score-row">
                <button
                  v-for="score in [1, 2, 3, 4, 5]"
                  :key="score"
                  type="button"
                  class="score-button"
                  @click="submitReviewScore(item, score)"
                >
                  {{ score }}
                </button>
              </div>
            </article>
            <p v-if="reviews.length === 0" class="empty-state">今日暂无复习项</p>
          </div>
        </section>
      </section>

      <section v-show="activeTab === 'plan'" class="two-column">
        <section class="panel">
          <h2>生成计划</h2>
          <form class="form-grid" @submit.prevent="submitPlan">
            <label class="field">
              目标
              <input v-model="planGoal" placeholder="例如：两周复习线性代数" />
            </label>
            <label class="field">
              科目
              <input v-model="planSubject" placeholder="可选" />
            </label>
            <div class="split-row">
              <label class="field">
                天数
                <input v-model.number="planDays" type="number" min="1" max="30" />
              </label>
              <label class="field">
                开始日期
                <input v-model="planStartDate" type="date" />
              </label>
            </div>
            <button type="submit" class="primary-button" :disabled="!planGoal.trim() || loading === 'plan'">
              生成
            </button>
          </form>
        </section>

        <section class="panel">
          <div class="panel-heading">
            <h2>计划结果</h2>
            <span v-if="planResult" class="counter">{{ planResult.created_tasks.length }} 任务</span>
          </div>
          <div v-if="planResult" class="plan-result">
            <p>{{ planResult.plan_text }}</p>
            <article v-for="day in planResult.days" :key="day.day" class="plan-day">
              <span>Day {{ day.day }} · {{ day.date }}</span>
              <strong>{{ day.title }}</strong>
              <p>{{ day.description }}</p>
            </article>
          </div>
          <p v-else class="empty-state">暂无计划</p>
        </section>
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
