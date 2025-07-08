<script setup>
import { onMounted, ref, reactive } from "vue";

import noUiSlider from 'nouislider';
import 'nouislider/dist/nouislider.css';
import Howler from "howler";
import SvgIcon from "@jamescoyle/vue-icon";
import { mdiVolumeHigh, mdiVolumeMute } from '@mdi/js';
import {globalSettings} from "../global_settings.js";

const DEFAULT_VOLUME = 70;

const emit = defineEmits(['volumeChange'])

function communicateVolumeChange(val) {
  emit('volumeChange', val)
}

function setVolume(volumeNumber) {
  globalSettings.volume = volumeNumber;
  Howler.Howler.volume(globalSettings.mute ? 0 : volumeNumber / 100);
}

const volumeLabel = ref(null);
const volumeIcon = ref(mdiVolumeHigh);

onMounted(() => {
  const volumeSlider = document.getElementById('volume-slider');

  noUiSlider.create(volumeSlider, {
    start: DEFAULT_VOLUME,
    connect: "lower",
    width: 100,
    range: {
      'min': 0,
      'max': 100
    },
    // behaviour: 'tap-drag',
    // tooltips: true,
    //handles : 1,
    //step : 1,
    orientation : "horizontal",
  });

  // 0 <= volumeNumber <= 100
  setVolume(DEFAULT_VOLUME);
  volumeSlider.noUiSlider.on('update', (value) => { setVolume(value) });
})

function volumeLabelClicked() {
  globalSettings.mute = ! globalSettings.mute;
  volumeIcon.value = globalSettings.mute ? mdiVolumeMute : mdiVolumeHigh;
  setVolume(globalSettings.volume);
}

</script>

<template>
  <div id="volume-settings">
    <label id="volume-label" ref="volumeLabel" for="volume-slider" @click="volumeLabelClicked()">
      <svg-icon class="volume_icon" type="mdi" :path="volumeIcon" size="30"></svg-icon>
    </label>
    <div id="volume-slider" aria-labelledby="volume-label"></div>
  </div>
</template>

<style scoped>

#volume-settings {
  display: flex;
  align-items: center;
  vertical-align: center;
  justify-content: space-between;
  margin-top: 0px;
}

#volume-label {
  margin-left: 15px;
  margin-right: 5px;
}

#volume-slider {
  display: flex;
  width: 100px;
  margin-left: 5px;
  margin-right: 5px;
}

.volume_icon {
  margin-top: 4px;
}

</style>
