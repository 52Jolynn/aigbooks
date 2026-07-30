<template>
  <div class="vote-button">
    <button
      type="button"
      class="vote-button__btn"
      :class="{ 'is-voted': userVote === 1 }"
      :disabled="loading"
      :aria-label="`Upvote (${report.upvote})`"
      @click="vote(1)"
    >
      ▲ <span class="vote-button__count">{{ report.upvote }}</span>
    </button>
    <button
      type="button"
      class="vote-button__btn vote-button__btn--down"
      :class="{ 'is-voted': userVote === -1 }"
      :disabled="loading"
      :aria-label="`Downvote (${report.downvote})`"
      @click="vote(-1)"
    >
      ▼ <span class="vote-button__count">{{ report.downvote }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { ReportOut } from '@/api/books';
import { voteReport } from '@/api/reports';
import { useFingerprintStore } from '@/stores/fingerprint';

const props = defineProps<{ report: ReportOut; userVote?: -1 | 0 | 1 }>();
const emit = defineEmits<{ voted: [ReportOut] }>();

const fpStore = useFingerprintStore();
const loading = ref(false);
const userVote = ref(props.userVote ?? 0);

async function vote(voteType: -1 | 1) {
  if (loading.value) return;
  loading.value = true;
  try {
    const fp = await fpStore.ensure();
    const { data } = await voteReport(props.report.id, voteType, fp);
    userVote.value = voteType;
    emit('voted', data);
  } catch (e) {
    console.error('Vote failed:', e);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.vote-button { display: inline-flex; gap: 8px; }
.vote-button__btn {
  background: var(--paper);
  border: 1px solid var(--rule);
  padding: 6px 12px;
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--ink);
  cursor: pointer;
  transition: all 0.2s;
}
.vote-button__btn:hover { border-color: var(--stamp-red); color: var(--stamp-red); }
.vote-button__btn.is-voted {
  border-color: var(--stamp-red);
  color: var(--stamp-red);
  background: var(--alert-bg);
}
.vote-button__btn--down { color: var(--ink-soft); }
.vote-button__count { font-weight: 700; margin-left: 4px; }
</style>
