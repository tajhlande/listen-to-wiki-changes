<script setup>
import {onMounted} from "vue";

import noUiSlider from 'nouislider';
import 'nouislider/dist/nouislider.css';
import Howler from "howler";

const DEFAULT_VOLUME = 70;

const emit = defineEmits(['volumeChange'])

function communicateVolumeChange(val) {
  emit('volumeChange', val)
}

function setVolume(volumeNumber) {
  Howler.Howler.volume(volumeNumber / 100);
}

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

</script>

<template>
  <div id="volume-settings">
    <label id="volume-label" for="volume-slider">Volume</label>
    <div id="volume-slider" aria-labelledby="volume-label"></div>
  </div>
</template>

<style scoped>

#volume-settings {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

#volume-label {
  margin-left: 15px;
  margin-right: 5px;
}

#volume-slider {
  display: flex;
  width: 100px;
  margin-left: 5px;
  margin-right: 40px;
}


</style>
