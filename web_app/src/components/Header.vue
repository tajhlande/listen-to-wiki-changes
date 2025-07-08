<script setup lang="ts">
import { ref } from 'vue';
import { CdxButton } from '@wikimedia/codex';
import { globalSettings, SPATIAL_POSITION, SPATIAL_PITCH, SPATIAL_MONO } from '../global_settings';
import VolumeSlider from "./VolumeSlider.vue";
import settings from "./Settings.vue";


function enable_default_wikis() {
  console.log("Button clicked. Emitting start-listening event");
  window.dispatchEvent(new CustomEvent("start-listening"));
}

// Track whether the settings pane is visible
const settingsExpanded = ref(false)

</script>

<template>
  <header>
    <h1>
      Listen To Wiki Changes
    </h1>
    <ul id="top-menu">
      <li><cdx-button id="start-button" size="medium" @click="enable_default_wikis">Start</cdx-button></li>
      <li><VolumeSlider></VolumeSlider></li>
      <li class="header-link"><a href="#about">About</a></li>
      <li class="header-link"><a href="#selector-container">Selector</a></li>
      <li class="header-link"><a href="#recent-changes-log">Recent Changes</a></li>
      <li class="header-link"><a href="#area">Visualization</a></li>
      <li>
        <cdx-button id="settings-button" @click="settingsExpanded = !settingsExpanded">
          <settings class="settings-gear"></settings>
        </cdx-button>

      </li>
    </ul>
    <!-- Settings pane -->
    <div v-if="settingsExpanded" class="settings-pane">
      <label>
        <input type="checkbox" v-model="globalSettings.showVisualizer" />
        Show Visualizer
      </label>
      <label>
        <input type="checkbox" v-model="globalSettings.showChangeLog" />
        Show Change Log
      </label>
      <label>
        <input type="checkbox" v-model="globalSettings.showWikiSelector" />
        Show Wikis Selector
      </label>

      <label>Stereo Positioning</label>
      <label>
        <input type="radio" :value="SPATIAL_POSITION" v-model="globalSettings.spatialAudio" />
        Screen Position
      </label>

      <label>
        <input type="radio" :value="SPATIAL_PITCH" v-model="globalSettings.spatialAudio" />
        Edit Size
      </label>

      <label>
        <input type="radio" :value="SPATIAL_MONO" v-model="globalSettings.spatialAudio" />
        Mono
      </label>

    </div>
  </header>
</template>

<style scoped>

#start-button {
  padding-top: 2px;
  padding-bottom: 2px;
  margin-top: 4px;
}

.header-link {
  margin-top: 8px;
}

#settings-button {
  margin-left: 16px;
  margin-top: 3px;
}

.settings-pane {
  position: absolute;
  top: 100%;
  right: 0;
  border: 1px solid #ccc;
  padding: 1rem;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  border-radius: 4px;
  backdrop-filter: blur(4px); /* optional: gives a frosted glass effect */
}

@media (prefers-color-scheme: light) {
  .settings-pane {
    background-color: rgba(255, 255, 255, 0.7); /* 70% opaque white */
  }
}
@media (prefers-color-scheme: dark) {
  .settings-pane {
    background-color: rgba(65, 65, 65, 0.7); /* 70% opaque white */
  }
}
</style>
