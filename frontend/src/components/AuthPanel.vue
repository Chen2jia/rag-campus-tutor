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

const submitLabel = computed(() => {
  if (loading.value) {
    return "处理中";
  }
  return authMode.value === "login" ? "登录" : "创建账号";
});

const authHelpText = computed(() => {
  if (authMode.value === "register") {
    return "用户名至少 2 个字符，密码至少 8 位。";
  }
  return "请输入注册时使用的邮箱和至少 8 位密码。";
});

function switchAuthMode(mode: "login" | "register") {
  authMode.value = mode;
  errorMessage.value = "";
}

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
    errorMessage.value = error instanceof Error ? error.message : "认证失败";
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
        @click="switchAuthMode('login')"
      >
        登录
      </button>
      <button
        type="button"
        :class="{ active: authMode === 'register' }"
        @click="switchAuthMode('register')"
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
        <input
          v-model="password"
          :autocomplete="authMode === 'login' ? 'current-password' : 'new-password'"
          type="password"
          minlength="8"
        />
      </label>
      <p class="auth-help">{{ authHelpText }}</p>
      <button type="submit" class="primary-button" :disabled="!canSubmitAuth || loading">
        {{ submitLabel }}
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

.auth-help {
  margin: -4px 0 0;
  color: #647084;
  font-size: 12px;
  line-height: 1.5;
}

.auth-error {
  margin: 14px 0 0;
  color: #b42318;
}
</style>
