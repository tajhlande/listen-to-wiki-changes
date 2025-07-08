<script setup>
import { CdxProgressBar } from '@wikimedia/codex';
import LanguagesSelector from './components/LanguagesSelector.vue';
import RecentChangesLog from './components/RecentChangesLog.vue';
import AudioVisualizer from './components/AudioVisualizer.vue';
import About from './components/About.vue'
import Header from './components/Header.vue'
</script>

<template>
  <body>
    <Header></Header>
    <main>
      <Suspense>
        <template #fallback>
          <cdx-progress-bar />
        </template>
        <div>
          <div id="header_spacer"></div>
          <AudioVisualizer></AudioVisualizer>
          <RecentChangesLog></RecentChangesLog>
          <LanguagesSelector></LanguagesSelector>
          <About></About>
        </div>
      </Suspense>
    </main>
  </body>
</template>

<style>
#header_spacer {
  padding-top: 48px;
}
</style>
