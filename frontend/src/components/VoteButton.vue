<template>
  <div class="vote-button">
    <button
      type="button"
      class="vote-button__btn"
      :class="{ 'is-voted': userVote === 1 }"
      :disabled="loading"
      :aria-label="vote.upvote(report.upvote)"
      @click="voteAction(1)"
    >
      ▲ <span class="vote-button__count">{{ report.upvote }}</span>
    </button>
    <button
      type="button"
      class="vote-button__btn vote-button__btn--down"
      :class="{ 'is-voted is-down': userVote === -1 }"
      :disabled="loading"
      :aria-label="vote.downvote(report.downvote)"
      @click="voteAction(-1)"
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
import { consoleMessages, vote } from '@/i18n/zh';

const props = defineProps<{ report: ReportOut; userVote?: -1 | 0 | 1 }>();
const emit = defineEmits<{ voted: [ReportOut] }>();

const fpStore = useFingerprintStore();
const loading = ref(false);
const userVote = ref(props.userVote ?? 0);

async function voteAction(voteType: -1 | 1) {
  if (loading.value) return;
  loading.value = true;
  try {
    const fp = await fpStore.ensure();
    const { data } = await voteReport(props.report.id, voteType, fp);
    userVote.value = voteType;
    emit('voted', data);
  } catch (e) {
    console.error(consoleMessages.voteFailed, e);
  } finally {
    loading.value = false;
  }
}
</script>