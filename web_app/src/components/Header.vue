<script setup lang="ts">
import { ref } from 'vue';
import { CdxButton } from '@wikimedia/codex';
import { globalSettings, SPATIAL_POSITION, SPATIAL_PITCH, SPATIAL_MONO } from '../global_settings';
import VolumeSlider from "./VolumeSlider.vue";
import settings from "./Settings.vue";
import SvgIcon from '@jamescoyle/vue-icon';
import { mdiMenu } from '@mdi/js';

function enable_default_wikis() {
  console.debug("Button clicked. Emitting start-listening event");
  window.dispatchEvent(new CustomEvent("start-listening"));
}

function deselect_all_wikis() {
  console.debug("Button clicked. Emitting stop-listening event");
  window.dispatchEvent(new CustomEvent("stop-listening"));
}

// Track whether hamburger menu is visible
const menuOpen = ref(false);


// Track whether the settings pane is visible
const settingsExpanded = ref(false)

</script>

<template>
  <header>
    <h1>Listen To Wiki Changes</h1>
    <cdx-button class="hamburger" @click="menuOpen = !menuOpen" aria-label="Toggle menu">
      <svg-icon type="mdi" :path="mdiMenu"></svg-icon>
    </cdx-button>
    <ul id="top-menu" :class="{ open: menuOpen }">
      <li><cdx-button id="start-button" size="medium" @click="enable_default_wikis">Start</cdx-button></li>
      <li><cdx-button id="stop-button" size="medium" @click="deselect_all_wikis">Stop</cdx-button></li>
      <li><VolumeSlider></VolumeSlider></li>
      <li id="about-menu-item" class="header-link"><a href="#about">About</a></li>
      <li id="selector-menu-item" class="header-link"><a href="#selector-container">Selector</a></li>
      <li id="recent-changes-menu-item" class="header-link"><a href="#recent-changes-log">Recent Changes</a></li>
      <li id="visualization-menu-item" class="header-link"><a href="#area">Visualization</a></li>
      <li id="settings-menu-item">
        <cdx-button id="settings-button" @click="settingsExpanded = !settingsExpanded">
          <settings class="settings-gear"></settings>
        </cdx-button>
      </li>
      <li id="show-visualizer-menu-item" class="header-link">
        <input type="checkbox" v-model="globalSettings.showVisualizer" />
        Show Visualizer
      </li>
      <li id="show-changelog-menu-item" class="header-link">
        <input type="checkbox" v-model="globalSettings.showChangeLog" />
        Show Change Log
      </li>
      <li id="show-wiki-selector-menu-item" class="header-link">
        <input type="checkbox" v-model="globalSettings.showWikiSelector" />
        Show Wikis Selector
      </li>
      <li id="spatial-audio-menu-item">
        <label>Stereo Positioning: </label>
        <span>
          <input type="radio" :value="SPATIAL_POSITION" v-model="globalSettings.spatialAudio" />
          Screen Position
        </span>
        <span>
          <input type="radio" :value="SPATIAL_PITCH" v-model="globalSettings.spatialAudio" />
          Edit Size
        </span>
        <span>
          <input type="radio" :value="SPATIAL_MONO" v-model="globalSettings.spatialAudio" />
          Mono
        </span>
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

header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  width: 100%;
  height: 3rem;
  background-color: rgba(255, 255, 255, 1);
  border-style: var(--border-style-base);
  border-width: 0;
  border-bottom-width: var(--border-width-base);
  border-color: var(--border-color-inverted);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
}


header h1 {
  font-size: var(--font-size-xx-large);
  font-weight: var(--font-weight-semi-bold);
}

header ul {
  display: flex;
  list-style: none;
  gap: .5rem;
  margin-block: 0;
}

header button {
  padding-top: 2px;
  padding-bottom: 2px;
  margin-top: 5px;
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

/* Hamburger menu styles */
.hamburger {
  display: none;
  margin-left: auto;
  z-index: 1100;
}

#show-visualizer-menu-item {
  display: none;
}

#show-changelog-menu-item {
  display: none;
}

#show-wiki-selector-menu-item {
  display: none;
}

#spatial-audio-menu-item {
  display: none;
}

/* shrink the title when the header gets too small for it */
@media (max-width: 1200px) {
  header h1  {
    font-size: var(--font-size-x-large);
  }
}

/* Mobile responsive header menu */
@media (max-width: 1083px) {
  header {
    flex-direction: row;
    align-items: flex-start;
    height: auto;
    padding-left: 1rem;
    padding-right: 1rem;
    padding-top: 10px;
  }

  header h1 {
      font-size: var(--font-size-medium);
  }

  header ul {
    display: flex;
    flex-direction: column;
  }

  .hamburger {
    display: inline-flex;
  }

  #top-menu {
    display: none;
    flex-direction: column;
    width: 100%;
    background: var(--background-color-base, #fff);
    position: absolute;
    top: 3.5rem;
    left: 0;
    z-index: 1001;
    padding: 1rem 0;
    border-bottom: 1px solid #ccc;
  }
  #top-menu.open {
    display: flex;
  }
  #top-menu li {
    margin: 0.5rem 1rem;
  }

  #about-menu-item {
    display: none;
  }
  #selector-menu-item {
    display: none;
  }
  #recent-changes-menu-item {
    display: none;
  }
  #visualization-menu-item {
    display: none;
  }

  li#settings-menu-item {
    display: none;
  }

  li#spatial-audio-menu-item {
    display: flex;
    flex-direction: column;
  }

  li#spatial-audio-menu-item span {
    margin-top: 1rem;
  }

}

/* light and dark mode style adjustments */
@media (prefers-color-scheme: light) {
  .settings-pane {
    background-color: rgba(255, 255, 255, 0.7); /* 70% opaque white */
  }
}

@media (prefers-color-scheme: dark) {
  .settings-pane {
    background-color: rgba(65, 65, 65, 0.7); /* 70% opaque dark gray */
  }

  header {
    background-color: rgba(65, 65, 65, 1.0);
  }
}

/* Mobile dark mode */
@media (prefers-color-scheme: dark) and (max-width: 1024px) {
  #top-menu {
    background: rgba(65, 65, 65, 1.0);
  }
}


</style>
