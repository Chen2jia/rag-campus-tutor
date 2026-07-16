<script setup lang="ts">
import { ref } from "vue";

import { createReview, listTodayReviews, rateReview, type ReviewRead } from "../api/client";

const props = defineProps<{
  token: string;
  reviews: ReviewRead[];
}>();

const emit = defineEmits<{
  "update:reviews": [reviews: ReviewRead[]];
  notice: [message: string];
  error: [message: string];
}>();

const reviewPoint = ref("");
const reviewSubject = ref("");
const reviewDate = ref(today());
const loading = ref("");

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

async function submitReview() {
  if (!props.token || !reviewPoint.value.trim()) {
    return;
  }
  await runPanelTask("review-create", async () => {
    await createReview(
      props.token,
      reviewPoint.value.trim(),
      reviewSubject.value.trim(),
      reviewDate.value,
    );
    reviewPoint.value = "";
    reviewSubject.value = "";
    reviewDate.value = today();
    emit("update:reviews", await listTodayReviews(props.token));
    emit("notice", "复习项已创建");
  });
}

async function submitReviewScore(item: ReviewRead, score: number) {
  if (!props.token) {
    return;
  }
  await runPanelTask(`review-${item.id}-${score}`, async () => {
    await rateReview(props.token, item.id, score);
    emit("update:reviews", await listTodayReviews(props.token));
    emit("notice", "复习进度已更新");
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
          {{ loading === "review-create" ? "创建中" : "创建复习项" }}
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
            <p>
              {{ item.subject || "未分类" }} | 间隔 {{ item.interval_days }} 天 | EF
              {{ item.ease_factor.toFixed(2) }}
            </p>
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

.panel-heading,
.score-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-heading {
  justify-content: space-between;
}

.field {
  display: grid;
  gap: 6px;
  color: #536070;
  font-size: 13px;
  font-weight: 700;
}

.primary-button,
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

.score-button {
  min-width: 38px;
  padding: 0;
  background: #e7ebf2;
  color: #23314a;
}

.review-item {
  display: grid;
  gap: 8px;
  border: 1px solid #e3e8ef;
  border-radius: 8px;
  padding: 12px;
  background: #fbfcfe;
}

.review-item strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.review-item p,
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

.score-row {
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 980px) {
  .two-column {
    grid-template-columns: 1fr;
  }
}
</style>
