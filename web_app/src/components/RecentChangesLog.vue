<script setup>
import { ref, watch } from "vue";
import {getWikiCodes, useRecentChange} from "../composition.js";

const { recentChange } = useRecentChange();
const listenCounter = ref(0);
const recentChanges = ref([]);

const wikiCodeMap = new Map(getWikiCodes().map(item => [item.wikiCode, item]));

watch(recentChange, () => {
  listenCounter.value++;
  if (recentChanges.value.length > 10) {
    recentChanges.value.shift();
  }
  recentChanges.value.push(recentChange.value.data);
});

function lengthChangeToText(lengthChange) {
  if (lengthChange === 0) {
    return '+0 bytes';
  }
  if (lengthChange > 0) {
    return '+' + lengthChange + ' bytes';
  }
  if (lengthChange < 0) {
    return '-' + -lengthChange + ' bytes';
  }
  return 'unknown change size';
}

function lengthChangeClass(lengthChange) {
  if (lengthChange > 0) {
    return 'grow-change';
  }
  if (lengthChange < 0) {
    return 'shrink-change';
  }
  return '';
}



// decodeURI(change.meta.uri)
</script>

<template>
  <div id="recent-changes-log" class="anchor-target">
    <div id="log">
      <TransitionGroup name="list" tag="ul">
        <li v-for="change in recentChanges" :key="change.id ?? change.log_id">
          <span v-if="change.event_type === 'edit'">
            {{ change.bot ? '&#129302;' : '' }}
            {{ `${change.user}` }} edited
            <a target="_blank" :href="change.title_url" :title="change.title">{{change.title}}</a>
            on {{ wikiCodeMap.get(change.code).displayName }}
            <span :class="lengthChangeClass(change.change_in_length)"> ({{ lengthChangeToText(change.change_in_length)}})</span>
          </span>
          <span v-if="change.event_type === 'new_page'" style="font-weight: bold">
            {{ change.bot ? '&#129302;' : '' }}
            {{ `${change.user}` }} created page
            <a target="_blank" :href="change.title_url" :title="change.title">{{change.title}}</a>
            on {{change.domain}}
            <span :class="lengthChangeClass(change.change_in_length)"> ({{ lengthChangeToText(change.change_in_length)}})</span>
          </span>
          <span v-if="change.event_type === 'new_user'" style="font-weight: bolder">
            Welcome
            <a target="_blank" :href="change.title_url" :title="change.title">{{ `${change.user}` }}</a>
            to {{change.domain}}!
          </span>
        </li>
      </TransitionGroup>
    </div>
    <div style="margin-bottom: 1rem; text-align: center">
      You have listened to a total of
      <span id="edit-counter"> {{ listenCounter }} changes</span>.
    </div>
  </div>
</template>

<style scoped>
#log {
  width: auto;
  height: 20rem;
  max-width: 800px;
  overflow: hidden;
  margin: 1rem auto;
  border-style: var(--border-style-base);
  border-width: var(--border-width-base);
  border-color: var(--border-color-inverted);
}

#edit-counter {
  color: var(--color-destructive);
}

.list-enter-active {
  transition: all 0.5s ease;
}
.list-enter-from {
  opacity: 0;
  transform: translateY(30px);
}

ul {
  list-style: none;
}

.grow-change {
  color: #2686cf;
}

.shrink-change {
  color: #de9332;
}
</style>
