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
        <div id="app-container">
          <div id="header-spacer"></div>
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
#header-spacer {
  padding-top: 48px;
}

#app-container {
  /*max-width: 960px;*/
  margin: 0 auto;
  padding: 0;
  display: flex;
  flex-direction: column;
  /*gap: 2rem;*/
}

@media (max-width: 768px) {
  #app-container {
    padding: 0.5rem;
    gap: 1.5rem;
  }

  #header-spacer {
    padding-top: 0;
  }
}

</style>
