<script setup lang="ts">
import { computed, ref } from "vue";

import { login, register, type TokenResponse } from "../api/client";

const emit = defineEmits<{
  authenticated: [response: TokenResponse];
}>();

const authMode = ref<"login" | "register">("login");
const username = ref("");
const email = ref("");
const password = ref("");
const loading = ref(false);
const errorMessage = ref("");

const canSubmitAuth = computed(() => {
  if (authMode.value === "register" && username.value.trim().length < 2) {
    return false;
  }
  return email.value.trim().length > 2 && password.value.length >= 8;
});

async function submitAuth() {
  if (!canSubmitAuth.value || loading.value) {
    return;
  }

  loading.value = true;
  errorMessage.value = "";
  try {
    const response =
      authMode.value === "login"
        ? await login(email.value.trim(), password.value)
        : await register(username.value.trim(), email.value.trim(), password.value);
    emit("authenticated", response);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "登录失败";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="auth-panel">
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
      <button type="submit" class="primary-button" :disabled="!canSubmitAuth || loading">
        {{ loading ? "处理中" : authMode === "login" ? "登录" : "创建账号" }}
      </button>
    </form>

    <p v-if="errorMessage" class="auth-error">{{ errorMessage }}</p>
  </section>
</template>

<style scoped>
.auth-panel {
  width: min(440px, 100%);
  max-width: 1240px;
  margin: 0 auto;
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
  border: 0;
  border-radius: 6px;
  background: #eef2f7;
  color: #536070;
  cursor: pointer;
  font: inherit;
}

.auth-tabs button.active {
  background: #172033;
  color: #ffffff;
}

.auth-form {
  display: grid;
  gap: 14px;
}

label {
  display: grid;
  gap: 6px;
  color: #536070;
  font-size: 13px;
  font-weight: 700;
}

input {
  width: 100%;
  min-height: 42px;
  border: 1px solid #d5dbe5;
  border-radius: 6px;
  padding: 0 12px;
  background: #ffffff;
  color: #172033;
  font: inherit;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
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

.auth-error {
  margin: 14px 0 0;
  color: #b42318;
}
</style>
