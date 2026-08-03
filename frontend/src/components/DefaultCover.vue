<template>
  <svg
    class="default-cover"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 240 320"
    role="img"
    :aria-label="ariaLabel"
  >
    <title>{{ ariaLabel }}</title>

    <defs>
      <pattern id="bag-grain" width="6" height="6" patternUnits="userSpaceOnUse">
        <rect width="6" height="6" fill="#F4F7F5" />
        <circle cx="1" cy="1" r="0.35" fill="#C4CCC7" opacity="0.45" />
        <circle cx="4" cy="4" r="0.35" fill="#C4CCC7" opacity="0.45" />
      </pattern>

      <path id="stamp-top-arc" d="M -34 0 A 34 34 0 0 1 34 0" fill="none" />
      <path id="stamp-bot-arc" d="M -32 6 A 32 32 0 0 0 32 6" fill="none" />
    </defs>

    <rect width="240" height="320" fill="#ECF2EE" />
    <rect
      x="6"
      y="6"
      width="228"
      height="308"
      rx="6"
      fill="url(#bag-grain)"
      stroke="#C4CCC7"
      stroke-width="0.6"
    />
    <rect
      x="12"
      y="12"
      width="216"
      height="296"
      rx="4"
      fill="none"
      stroke="#C4CCC7"
      stroke-width="0.5"
      stroke-dasharray="2 3"
    />

    <g class="dc-mono" fill="#4A5650">
      <text x="18" y="26" font-size="6.5" letter-spacing="1.6">
        AIGBOOKS · QUARANTINE LEDGER
      </text>
    </g>

    <g class="dc-cn-display" fill="#0B5D47">
      <text x="20" y="78" font-size="34" font-weight="700" letter-spacing="2">默认封面</text>
    </g>
    <g class="dc-mono" fill="#4A5650">
      <text x="20" y="94" font-size="8.5" letter-spacing="0.6" fill="#1F2A24">
        DEFAULT COVER
      </text>
      <text x="20" y="107" font-size="7.5" letter-spacing="0.4">
        NO ORIGINAL ARTIFACT ATTACHED
      </text>
    </g>

    <line x1="20" y1="123" x2="220" y2="123" stroke="#C4CCC7" stroke-width="0.5" />
    <g class="dc-mono" font-size="6" fill="#6E7973" letter-spacing="1.2">
      <text x="20" y="132">SPECIMEN · 样本</text>
      <text x="220" y="132" text-anchor="end">REC · 归档中</text>
    </g>

    <g transform="translate(120 178)">
      <circle r="44" fill="#FFFFFF" stroke="#0E6B52" stroke-width="1.4" />
      <circle r="40" fill="none" stroke="#0E6B52" stroke-width="0.4" opacity="0.5" />
      <circle r="36" fill="none" stroke="#0E6B52" stroke-width="0.4" />

      <text class="dc-mono" font-size="6.2" fill="#0E6B52" letter-spacing="2.6">
        <textPath href="#stamp-top-arc" startOffset="50%" text-anchor="middle">
          AIG · QUARANTINE · INSP
        </textPath>
      </text>
      <text class="dc-mono" font-size="5.6" fill="#0E6B52" letter-spacing="3">
        <textPath href="#stamp-bot-arc" startOffset="50%" text-anchor="middle">
          EST · MMXXVI · UNIT 03
        </textPath>
      </text>

      <g transform="translate(0 -2)">
        <circle r="13" fill="none" stroke="#0B5D47" stroke-width="0.9" />
        <circle r="8" fill="none" stroke="#0B5D47" stroke-width="0.6" />
        <circle r="2.4" fill="#0B5D47" />
        <line x1="-13" y1="0" x2="-9" y2="0" stroke="#0B5D47" stroke-width="0.6" />
        <line x1="9" y1="0" x2="13" y2="0" stroke="#0B5D47" stroke-width="0.6" />
        <line x1="0" y1="-13" x2="0" y2="-9" stroke="#0B5D47" stroke-width="0.6" />
        <line x1="0" y1="9" x2="0" y2="13" stroke="#0B5D47" stroke-width="0.6" />
      </g>

      <text
        class="dc-mono"
        y="26"
        text-anchor="middle"
        font-size="6.5"
        fill="#0B5D47"
        letter-spacing="0.6"
      >
        AIG-0000-00-0000
      </text>
    </g>

    <line x1="20" y1="246" x2="220" y2="246" stroke="#C4CCC7" stroke-width="0.5" />
    <g class="dc-mono" letter-spacing="0.6">
      <text x="20" y="260" font-size="6" fill="#6E7973">TYPE 类型</text>
      <text x="20" y="272" font-size="6.5" fill="#1F2A24">{{ typeValue }}</text>

      <text x="120" y="260" font-size="6" fill="#6E7973">IDENT 编号</text>
      <text x="120" y="272" font-size="6.5" fill="#1F2A24">{{ identValue }}</text>

      <text x="20" y="292" font-size="6" fill="#6E7973">TITLE 书名</text>
      <text x="20" y="304" font-size="6.5" fill="#1F2A24">{{ titleValue }}</text>

      <text x="120" y="292" font-size="6" fill="#6E7973">AUTHOR 作者</text>
      <text x="120" y="304" font-size="6.5" fill="#1F2A24">{{ authorValue }}</text>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type IdentifierType = 'isbn' | 'issn' | 'issn-l';

const TYPE_LABEL: Record<IdentifierType, string> = {
  isbn: 'ISBN',
  issn: 'ISSN',
  'issn-l': 'ISSN-L',
};

const MAX_FIELD = 14;

const props = defineProps<{
  ariaLabel?: string;
  type?: IdentifierType;
  identifier?: string;
  title?: string;
  author?: string;
  reportCount?: number;
  createdAt?: string;
}>();

function truncate(value: string | undefined): string {
  if (!value) return '—';
  return value.length > MAX_FIELD ? value.slice(0, MAX_FIELD - 1) + '…' : value;
}

const typeValue = computed(() =>
  props.type ? (TYPE_LABEL[props.type] ?? '—') : '—',
);
const identValue = computed(() => truncate(props.identifier));
const titleValue = computed(() => truncate(props.title));
const authorValue = computed(() => truncate(props.author));
</script>

<style scoped>
.default-cover {
  display: block;
  width: 100%;
  height: 100%;
}
.default-cover .dc-mono {
  font-family: var(--font-mono);
}
.default-cover .dc-cn-display {
  font-family: var(--font-cn-display);
}
.default-cover text {
  text-rendering: geometricPrecision;
}
</style>
