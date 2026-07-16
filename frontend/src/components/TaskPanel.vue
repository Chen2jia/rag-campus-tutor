<script setup lang="ts">
import { computed, ref } from "vue";

import {
  createTask,
  deleteTask,
  listTasks,
  updateTask,
  type TaskRead,
} from "../api/client";

const props = defineProps<{
  token: string;
  tasks: TaskRead[];
}>();

const emit = defineEmits<{
  "update:tasks": [tasks: TaskRead[]];
  notice: [message: string];
  error: [message: string];
}>();

const taskTitle = ref("");
const taskSubject = ref("");
const taskPriority = ref(3);
const taskDueDate = ref("");
const loading = ref("");

const openTasks = computed(() => props.tasks.filter((task) => !task.is_done));
const doneTasks = computed(() => props.tasks.filter((task) => task.is_done));

async function submitTask() {
  if (!props.token || !taskTitle.value.trim()) {
    return;
  }
  await runPanelTask("task-create", async () => {
    await createTask(props.token, {
      title: taskTitle.value.trim(),
      subject: taskSubject.value.trim() || null,
      priority: taskPriority.value,
      due_date: taskDueDate.value || null,
    });
    taskTitle.value = "";
    taskSubject.value = "";
    taskPriority.value = 3;
    taskDueDate.value = "";
    emit("update:tasks", await listTasks(props.token));
    emit("notice", "任务已创建");
  });
}

async function toggleTask(task: TaskRead) {
  if (!props.token) {
    return;
  }
  await runPanelTask(`task-${task.id}`, async () => {
    const updated = await updateTask(props.token, task.id, { is_done: !task.is_done });
    emit(
      "update:tasks",
      props.tasks.map((item) => (item.id === updated.id ? updated : item)),
    );
  });
}

async function removeTask(task: TaskRead) {
  if (!props.token) {
    return;
  }
  await runPanelTask(`delete-${task.id}`, async () => {
    await deleteTask(props.token, task.id);
    emit(
      "update:tasks",
      props.tasks.filter((item) => item.id !== task.id),
    );
    emit("notice", "任务已删除");
  });
}

async function runPanelTask(name: string, task: () => Promise<void>) {
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
  <section class="two-column">
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
          {{ loading === "task-create" ? "创建中" : "创建任务" }}
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
            <p>{{ task.subject || "未分类" }} | P{{ task.priority }} | {{ task.due_date || "无截止" }}</p>
          </div>
          <button type="button" class="small-button" @click="removeTask(task)">删除</button>
        </article>
        <article v-for="task in doneTasks" :key="task.id" class="task-item done">
          <input type="checkbox" :checked="task.is_done" @change="toggleTask(task)" />
          <div>
            <strong>{{ task.title }}</strong>
            <p>{{ task.subject || "未分类" }} | 已完成</p>
          </div>
          <button type="button" class="small-button" @click="removeTask(task)">删除</button>
        </article>
        <p v-if="tasks.length === 0" class="empty-state">暂无任务</p>
      </div>
    </section>
  </section>
</template>

<style scoped>
h2,
p {
  margin: 0;
}

h2 {
  font-size: 18px;
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

.two-column {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.panel,
.form-grid,
.item-list {
  display: grid;
  gap: 14px;
}

.panel {
  align-content: start;
  border: 1px solid #dfe4ec;
  border-radius: 8px;
  padding: 16px;
  background: #ffffff;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.field {
  display: grid;
  gap: 6px;
  color: #536070;
  font-size: 13px;
  font-weight: 700;
}

.split-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.primary-button,
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

.small-button {
  background: #e7ebf2;
  color: #23314a;
}

.task-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  border: 1px solid #e3e8ef;
  border-radius: 8px;
  padding: 12px;
  background: #fbfcfe;
}

.task-item.done strong {
  color: #7a8596;
  text-decoration: line-through;
}

.task-item strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-item p,
.empty-state {
  color: #536070;
  line-height: 1.55;
}

.counter {
  border-radius: 999px;
  padding: 4px 8px;
  background: #edf1f6;
  color: #536070;
  font-size: 12px;
}

@media (max-width: 980px) {
  .two-column {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .split-row {
    grid-template-columns: 1fr;
  }
}
</style>
