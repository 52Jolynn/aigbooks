<template>
  <footer class="colophon">
    <p>
      {{ colophon.line1 }}<strong>{{ colophon.line1Bold }}</strong>{{ colophon.line1Tail }}
      {{ colophon.line2 }}
    </p>
    <p style="margin-top:12px;font-size:12px;">{{ colophon.line3 }}</p>
  </footer>
</template>

<script setup lang="ts">
import { colophon } from '@/i18n/zh';
</script>