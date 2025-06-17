<script setup lang="ts">
import { CdxButton } from '@wikimedia/codex';
import VolumeSlider from "./VolumeSlider.vue";

function enable_en_wiki() {
  console.log("Button clicked. Emitting start-listening event");
  window.dispatchEvent(new CustomEvent("start-listening"));
}

</script>

<template>
  <header>
    <h1>
      Listen To Wiki Changes
    </h1>
    <ul>
      <li><cdx-button id="start-button" size="medium" @click="enable_en_wiki">Start</cdx-button></li>
      <li><VolumeSlider></VolumeSlider></li>
      <li class="header-link"><a href="#about">About</a></li>
      <li class="header-link"><a href="#selector-container">Selector</a></li>
      <li class="header-link"><a href="#recent-changes-log">Recent Changes</a></li>
      <li class="header-link"><a href="#area">Visualization</a></li>
    </ul>
  </header>

</template>

<style scoped>

#start-button {
  padding-top: 2px;
  padding-bottom: 2px;
}

.header-link {
  margin-top: 4px;
}

</style>
