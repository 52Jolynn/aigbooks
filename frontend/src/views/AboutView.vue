<template>
  <main class="ledger">
    <SectionHeader
      :num="about.sectionNum"
      :title="about.sectionTitle"
      :meta="about.sectionMeta"
    />

    <section class="disclaimer" aria-label="关于本站">
      <span class="disclaimer__icon" aria-hidden="true">✦</span>
      <div>
        <p>{{ about.intro }}</p>
      </div>
    </section>

    <article>
      <h3 class="about-heading">{{ about.intent.heading }}</h3>
      <p>{{ about.intent.p1 }}</p>
      <p>{{ about.intent.p2 }}</p>

      <h3 class="about-heading">{{ about.principles.heading }}</h3>
      <ul class="about-principles">
        <li v-for="(item, i) in about.principles.items" :key="i">{{ item }}</li>
      </ul>
      <p>{{ about.principles.note }}</p>

      <h3 class="about-heading">{{ about.terms.heading }}</h3>
      <aside class="book-detail__warning" role="note">
        <p>{{ about.terms.p1 }}</p>
        <p>{{ about.terms.p2 }}</p>
        <p>{{ about.terms.p3 }}</p>
      </aside>

      <p class="about-signoff">{{ about.signoff }}</p>
    </article>
  </main>
</template>

<script setup lang="ts">
import SectionHeader from '@/components/SectionHeader.vue';
import { about } from '@/i18n/zh';
</script>

<style scoped>
.about-heading {
  font-family: var(--font-cn-display);
  font-size: 20px;
  color: var(--ink-deep);
  margin: 48px 0 16px;
  letter-spacing: 0.04em;
}
.about-principles {
  list-style: none;
  padding: 0;
  margin: 0 0 16px;
}
.about-principles li {
  position: relative;
  padding: 10px 0 10px 28px;
  border-bottom: 1px dashed var(--surface-rule);
  font-family: var(--font-cn);
  color: var(--ink);
  line-height: 1.75;
}
.about-principles li::before {
  content: '§';
  position: absolute;
  left: 0;
  top: 10px;
  color: var(--quarantine-ok);
  font-family: var(--font-mono);
  font-size: 13px;
  letter-spacing: 0.08em;
}
.about-signoff {
  margin-top: 56px;
  text-align: center;
  font-family: var(--font-cn);
  color: var(--ink-faint);
  font-size: 14px;
  letter-spacing: 0.06em;
}
</style>