<script setup lang="ts">
import { computed, ref } from "vue";

import { streamChat, type RagSource } from "../api/client";

type ChatIntent = "knowledge" | "plan" | "general";

type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  text: string;
  intent: ChatIntent | null;
  isPlaceholder: boolean;
  answerProvider: string;
  model: string | null;
  sources: RagSource[];
  contextText: string;
  createdTasks: string[];
  errorMessage: string | null;
};

const props = defineProps<{
  token: string;
  selectedDocumentId: string;
  selectedDocumentName: string;
}>();

const input = ref("");
const loading = ref(false);
const messages = ref<ChatMessage[]>([]);
const nextId = ref(1);

const scopeLabel = computed(() =>
  props.selectedDocumentName.trim() ? props.selectedDocumentName : "全部资料",
);

async function sendMessage() {
  const text = input.value.trim();
  if (!props.token || !text || loading.value) {
    return;
  }

  const userMessage: ChatMessage = {
    id: nextId.value++,
    role: "user",
    text,
    intent: null,
    isPlaceholder: true,
    answerProvider: "user",
    model: null,
    sources: [],
    contextText: "",
    createdTasks: [],
    errorMessage: null,
  };
  const assistantId = nextId.value++;
  const assistantMessage: ChatMessage = {
    id: assistantId,
    role: "assistant",
    text: "",
    intent: null,
    isPlaceholder: true,
    answerProvider: "placeholder",
    model: null,
    sources: [],
    contextText: "",
    createdTasks: [],
    errorMessage: null,
  };

  messages.value = [...messages.value, userMessage, assistantMessage];
  input.value = "";
  loading.value = true;

  try {
    await streamChat(props.token, text, props.selectedDocumentId, (event) => {
      patchMessage(assistantId, event);
    });
  } catch (error) {
    patchMessage(assistantId, {
      event: "error",
      data: {
        message: error instanceof Error ? error.message : "对话发送失败",
      },
    });
  } finally {
    loading.value = false;
  }
}

function patchMessage(
  messageId: number,
  event:
    | { event: "start"; data: { message: string; intent: ChatIntent } }
    | {
        event: "content";
        data: {
          text?: string;
          intent?: ChatIntent;
          is_placeholder?: boolean;
          answer_provider?: string;
          model?: string | null;
          created_tasks?: string[];
        };
      }
    | { event: "citations"; data: { sources: RagSource[]; context_text: string } }
    | { event: "done"; data: { intent?: ChatIntent } }
    | { event: "error"; data: { message: string } },
) {
  messages.value = messages.value.map((message) => {
    if (message.id !== messageId) {
      return message;
    }

    if (event.event === "start") {
      return { ...message, intent: event.data.intent };
    }

    if (event.event === "content") {
      return {
        ...message,
        intent: event.data.intent ?? message.intent,
        text: event.data.text ?? message.text,
        isPlaceholder: event.data.is_placeholder ?? message.isPlaceholder,
        answerProvider: event.data.answer_provider ?? message.answerProvider,
        model: event.data.model ?? message.model,
        createdTasks: event.data.created_tasks ?? message.createdTasks,
      };
    }

    if (event.event === "citations") {
      return {
        ...message,
        sources: event.data.sources,
        contextText: event.data.context_text,
      };
    }

    if (event.event === "done") {
      return { ...message };
    }

    return {
      ...message,
      errorMessage: event.data.message,
    };
  });
}
</script>

<template>
  <section class="chat-panel">
    <div class="chat-header">
      <div>
        <h2>对话</h2>
        <p>当前范围：{{ scopeLabel }}</p>
      </div>
      <span class="chat-status">{{ loading ? "生成中" : "就绪" }}</span>
    </div>

    <div class="chat-history" aria-live="polite">
      <article v-for="message in messages" :key="message.id" :class="['bubble', message.role]">
        <div class="bubble-meta">
          <span>{{ message.role === "user" ? "你" : "助手" }}</span>
          <span v-if="message.intent">{{ message.intent }}</span>
          <span v-if="message.answerProvider">{{ message.answerProvider }}</span>
          <span v-if="message.model">{{ message.model }}</span>
          <span v-if="message.errorMessage" class="error-chip">错误</span>
        </div>
        <p class="bubble-text">{{ message.text || "..." }}</p>
        <div v-if="message.createdTasks.length > 0" class="source-list">
          <span v-for="taskId in message.createdTasks" :key="taskId">任务 {{ taskId }}</span>
        </div>
        <div v-if="message.sources.length > 0" class="source-list">
          <span v-for="source in message.sources" :key="`${source.document_id}-${source.chunk_index}`">
            {{ source.filename }} | {{ source.path }} | {{ source.page_start }}-{{ source.page_end }}
          </span>
        </div>
        <p v-if="message.contextText" class="context-text">{{ message.contextText }}</p>
        <p v-if="message.errorMessage" class="error-text">{{ message.errorMessage }}</p>
      </article>
      <p v-if="messages.length === 0" class="empty-state">
        先问一句试试，例如“帮我生成 3 天复习计划”或“总结这份资料的重点”。
      </p>
    </div>

    <form class="chat-form" @submit.prevent="sendMessage">
      <textarea
        v-model="input"
        rows="4"
        placeholder="输入问题、学习目标，或让助手基于资料回答"
      />
      <button type="submit" class="primary-button" :disabled="loading || !input.trim()">
        {{ loading ? "发送中" : "发送" }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.chat-panel {
  display: grid;
  gap: 14px;
  border: 1px solid #dfe4ec;
  border-radius: 8px;
  padding: 16px;
  background: #ffffff;
}

.chat-header,
.bubble-meta,
.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chat-header {
  align-items: center;
  justify-content: space-between;
}

.chat-header p {
  margin-top: 4px;
  color: #536070;
  font-size: 13px;
}

.chat-status,
.bubble-meta span,
.source-list span {
  border-radius: 999px;
  background: #edf1f6;
  color: #536070;
  padding: 4px 8px;
  font-size: 12px;
}

.chat-history {
  display: grid;
  gap: 10px;
  max-height: 540px;
  overflow: auto;
}

.bubble {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid #e3e8ef;
  border-radius: 8px;
  background: #fbfcfe;
}

.bubble.user {
  margin-left: 48px;
  background: #f0f6ff;
}

.bubble.assistant {
  margin-right: 48px;
}

.bubble-text,
.context-text {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #172033;
}

.context-text {
  color: #536070;
  font-size: 13px;
}

.empty-state {
  margin: 0;
  color: #536070;
}

.error-chip,
.error-text {
  color: #b42318;
}

.chat-form {
  display: grid;
  gap: 10px;
}

textarea {
  width: 100%;
  resize: vertical;
  min-height: 120px;
  border: 1px solid #d5dbe5;
  border-radius: 6px;
  padding: 10px 12px;
  font: inherit;
}

.primary-button {
  min-height: 38px;
  border: 0;
  border-radius: 6px;
  padding: 0 14px;
  background: #2454d6;
  color: #ffffff;
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  white-space: nowrap;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
</style>
