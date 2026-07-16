<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";

import {
  askRag,
  deleteDocument,
  getDocumentStatus,
  listDocuments,
  searchDocumentChunks,
  uploadDocument,
  type DocumentChunkSearchResult,
  type DocumentRead,
  type DocumentStatusResponse,
  type RagAskResponse,
} from "../api/client";

const props = defineProps<{
  token: string;
  documents: DocumentRead[];
  selectedDocumentId: string;
}>();

const emit = defineEmits<{
  "update:documents": [documents: DocumentRead[]];
  "update:selectedDocumentId": [documentId: string];
  notice: [message: string];
  error: [message: string];
}>();

const selectedFile = ref<File | null>(null);
const searchQuery = ref("");
const searchResults = ref<DocumentChunkSearchResult[]>([]);
const question = ref("");
const ragAnswer = ref<RagAskResponse | null>(null);
const loading = ref("");
const pollingStatus = ref<DocumentStatusResponse | null>(null);
const pollingTimer = ref<number | null>(null);

const DOCUMENT_STATUS_POLL_INTERVAL_MS = 1200;
const DOCUMENT_STATUS_MAX_ATTEMPTS = 20;

const selectedDocumentName = computed(() => {
  if (!props.selectedDocumentId) {
    return "全部资料";
  }
  return (
    props.documents.find((document) => document.id === props.selectedDocumentId)?.filename ??
    "已选资料"
  );
});

onBeforeUnmount(() => {
  clearDocumentPoll();
});

function selectDocument(documentId: string) {
  emit("update:selectedDocumentId", documentId);
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
}

async function refreshDocuments() {
  if (!props.token) {
    return;
  }
  await runLibraryTask("documents", async () => {
    await loadDocumentsData();
    emit("notice", "资料列表已刷新");
  });
}

async function loadDocumentsData() {
  const nextDocuments = await listDocuments(props.token);
  emit("update:documents", nextDocuments);
  if (
    props.selectedDocumentId &&
    !nextDocuments.some((document) => document.id === props.selectedDocumentId)
  ) {
    emit("update:selectedDocumentId", "");
  }
}

async function submitUpload() {
  if (!props.token || !selectedFile.value) {
    return;
  }
  await runLibraryTask("upload", async () => {
    const response = await uploadDocument(props.token, selectedFile.value as File);
    selectedFile.value = null;
    await loadDocumentsData();
    await waitForDocumentProcessing(response.task_id);
  });
}

async function deleteDocumentItem(document: DocumentRead) {
  if (!props.token) {
    return;
  }
  const confirmed = window.confirm(`确定删除资料「${document.filename}」吗？`);
  if (!confirmed) {
    return;
  }

  await runLibraryTask(`document-delete-${document.id}`, async () => {
    await deleteDocument(props.token, document.id);
    if (props.selectedDocumentId === document.id) {
      emit("update:selectedDocumentId", "");
    }
    searchResults.value = [];
    ragAnswer.value = null;
    await loadDocumentsData();
    emit("notice", "资料已删除");
  });
}

async function waitForDocumentProcessing(taskId: string) {
  clearDocumentPoll();

  for (let attempt = 0; attempt < DOCUMENT_STATUS_MAX_ATTEMPTS; attempt += 1) {
    const status = await getDocumentStatus(props.token, taskId);
    pollingStatus.value = status;
    await loadDocumentsData();

    if (isFailedStatus(status.status)) {
      throw new Error(status.error_message ?? "PDF 处理失败");
    }

    if (isTerminalStatus(status.status)) {
      emit("notice", `PDF 已处理完成：${status.total_chunks} 个片段`);
      clearDocumentPoll();
      return;
    }

    await waitForNextPoll();
  }

  emit("notice", "PDF 已上传，仍在处理中，请稍后刷新资料列表");
  clearDocumentPoll();
}

function waitForNextPoll(): Promise<void> {
  return new Promise((resolve) => {
    pollingTimer.value = window.setTimeout(() => {
      pollingTimer.value = null;
      resolve();
    }, DOCUMENT_STATUS_POLL_INTERVAL_MS);
  });
}

function clearDocumentPoll() {
  if (pollingTimer.value !== null) {
    window.clearTimeout(pollingTimer.value);
    pollingTimer.value = null;
  }
}

function isTerminalStatus(status: string) {
  return ["processed", "done", "failed"].includes(status);
}

function isFailedStatus(status: string) {
  return status === "failed";
}
async function submitSearch() {
  if (!props.token || !searchQuery.value.trim()) {
    return;
  }
  await runLibraryTask("search", async () => {
    const response = await searchDocumentChunks(
      props.token,
      searchQuery.value.trim(),
      props.selectedDocumentId,
    );
    searchResults.value = response.results;
    emit("notice", `找到 ${response.total} 个片段`);
  });
}

async function submitQuestion() {
  if (!props.token || !question.value.trim()) {
    return;
  }
  await runLibraryTask("rag", async () => {
    ragAnswer.value = await askRag(props.token, question.value.trim(), props.selectedDocumentId);
    emit("notice", ragAnswer.value.is_placeholder ? "已返回检索上下文" : "已生成回答");
  });
}

async function runLibraryTask(name: string, task: () => Promise<void>) {
  loading.value = name;
  emit("error", "");
  emit("notice", "");
  try {
    await task();
  } catch (error) {
    emit("error", error instanceof Error ? error.message : "操作失败");
  } finally {
    loading.value = "";
  }
}
</script>

<template>
  <section class="library-grid">
    <aside class="panel document-panel">
      <div class="panel-heading">
        <div>
          <h2>资料</h2>
          <p class="panel-subtitle">当前范围：{{ selectedDocumentName }}</p>
        </div>
        <button type="button" class="ghost-button" @click="refreshDocuments">刷新</button>
      </div>

      <form class="upload-row" @submit.prevent="submitUpload">
        <input type="file" accept="application/pdf" @change="handleFileChange" />
        <button type="submit" class="primary-button" :disabled="!selectedFile || loading === 'upload'">
          {{ loading === "upload" ? "处理中" : "上传" }}
        </button>
      </form>

      <p
        v-if="pollingStatus"
        class="polling-state"
        :class="{ failed: isFailedStatus(pollingStatus.status) }"
      >
        PDF 状态：{{ pollingStatus.status }}，{{ pollingStatus.total_chunks }} 个片段
        <span v-if="pollingStatus.error_message"> | {{ pollingStatus.error_message }}</span>
      </p>

      <label class="field">
        文档范围
        <select :value="selectedDocumentId" @change="selectDocument(($event.target as HTMLSelectElement).value)">
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
            <p>{{ document.total_chunks }} chunks | {{ document.status }}</p>
          </div>
          <div class="document-actions">
            <button type="button" class="small-button" @click="selectDocument(document.id)">选择</button>
            <button
              type="button"
              class="small-button danger-button"
              :disabled="loading === `document-delete-${document.id}`"
              @click="deleteDocumentItem(document)"
            >
              {{ loading === `document-delete-${document.id}` ? "删除中" : "删除" }}
            </button>
          </div>
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
                <span v-if="result.contains_formula">包含公式</span>
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
                {{ source.filename }} | {{ source.path }} | {{ source.page_start }}-{{ source.page_end }}
              </span>
            </div>
          </article>
          <p v-else class="empty-state">暂无回答</p>
        </section>
      </div>
    </section>
  </section>
</template>

<style scoped>
h2,
h3,
p {
  margin: 0;
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

.panel-heading,
.query-row,
.upload-row,
.answer-meta,
.result-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.document-panel,
.tool-panel,
.panel {
  display: grid;
  gap: 14px;
}

.field {
  display: grid;
  gap: 6px;
  color: #536070;
  font-size: 13px;
  font-weight: 700;
}

.panel-subtitle {
  margin-top: 4px;
  color: #647084;
  font-size: 13px;
}

.polling-state {
  color: #536070;
  font-size: 13px;
}

.polling-state.failed {
  color: #b42318;
}

.library-grid {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 18px;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
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

.document-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.danger-button {
  background: #f8d7da;
  color: #8a1f2d;
}

.result-item,
.answer-box {
  display: grid;
  gap: 8px;
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

.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 980px) {
  .library-grid,
  .tool-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .query-row,
  .upload-row {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
