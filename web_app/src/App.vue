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
          <AudioVisualizer></AudioVisualizer>
          <RecentChangesLog></RecentChangesLog>
          <LanguagesSelector></LanguagesSelector>
          <About></About>
        </div>
      </Suspense>
    </main>
  </body>
</template>
