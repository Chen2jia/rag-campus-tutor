<script setup lang="ts">
import { ref } from "vue";

import { generatePlan, listTasks, type PlanGenerateResponse, type TaskRead } from "../api/client";

const props = defineProps<{
  token: string;
  planResult: PlanGenerateResponse | null;
}>();

const emit = defineEmits<{
  "update:planResult": [planResult: PlanGenerateResponse | null];
  "update:tasks": [tasks: TaskRead[]];
  notice: [message: string];
  error: [message: string];
}>();

const planGoal = ref("");
const planDays = ref(7);
const planSubject = ref("");
const planStartDate = ref(today());
const loading = ref("");

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

async function submitPlan() {
  if (!props.token || !planGoal.value.trim()) {
    return;
  }
  await runPanelTask("plan", async () => {
    const nextPlanResult = await generatePlan(
      props.token,
      planGoal.value.trim(),
      planDays.value,
      planSubject.value.trim(),
      planStartDate.value,
    );
    emit("update:planResult", nextPlanResult);
    emit("update:tasks", await listTasks(props.token));
    emit("notice", `已生成 ${nextPlanResult.days.length} 天计划`);
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
          {{ loading === "plan" ? "生成中" : "生成" }}
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
          <span>Day {{ day.day }} | {{ day.date }}</span>
          <strong>{{ day.title }}</strong>
          <p>{{ day.description }}</p>
        </article>
      </div>
      <p v-else class="empty-state">暂无计划</p>
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
input {
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

input {
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
.plan-result {
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

.primary-button {
  min-height: 38px;
  border-radius: 6px;
  padding: 0 14px;
  background: #2454d6;
  color: #ffffff;
  font-weight: 700;
  white-space: nowrap;
}

.plan-day {
  display: grid;
  gap: 8px;
  border: 1px solid #e3e8ef;
  border-radius: 8px;
  padding: 12px;
  background: #fbfcfe;
}

.plan-day strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-result p,
.plan-day p,
.empty-state {
  color: #536070;
  line-height: 1.55;
}

.counter,
.plan-day span {
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
