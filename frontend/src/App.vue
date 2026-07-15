<template>
  <main class="app-shell">
    <section class="hero">
      <p class="eyebrow">EduMate</p>
      <h1>Multi-agent campus learning assistant</h1>
      <p class="summary">
        Phase 1 skeleton is ready. Authentication, RAG, planning, and harness
        checks will be added module by module.
      </p>
    </section>
  </main>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 48px;
  background: #f6f7fb;
  color: #172033;
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;
}

.hero {
  width: min(720px, 100%);
}

.eyebrow {
  margin: 0 0 12px;
  color: #3563e9;
  font-weight: 700;
}

h1 {
  margin: 0;
  font-size: 40px;
  line-height: 1.1;
}

.summary {
  margin: 18px 0 0;
  max-width: 620px;
  color: #556070;
  font-size: 18px;
  line-height: 1.6;
}
</style>

