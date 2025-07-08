import { reactive } from 'vue'

// Defaults go here!

export const SPATIAL_POSITION = 'position';
export const SPATIAL_PITCH = 'pitch';
export const SPATIAL_MONO = 'mono';

export const globalSettings = reactive({
    volume: 70, // 0 to 100
    mute: false,
    showVisualizer: true,
    showChangeLog: true,
    showWikiSelector: true,
    spatialAudio: SPATIAL_POSITION,
    stub: null
})


