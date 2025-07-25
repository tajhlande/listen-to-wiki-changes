import {Howl} from "howler";

export let celesta = []
export let clav = []
export let swells = []

export function calculateSize(data) {
    try {
        const scale_factor = 5
        let orig_size = data.change_in_length; // data.length.new - data.length.old
        const abs_size = Math.abs(orig_size);
        let scaled_size = Math.max(Math.sqrt(abs_size) * scale_factor, 3);
        return [orig_size, scaled_size];
    } catch (e) {
        console.log(e);
        console.log(JSON.stringify(data));
        return [0, 0];
    }
}

export function loadSounds() {
    // load celesta and clav sounds
    let filename = null
    for (let i = 1; i <= 24; i++) {
        if (i > 9) {
            filename = 'c0' + i
        } else {
            filename = 'c00' + i
        }
        celesta.push(new Howl({
            src : ['sounds/celesta/' + filename + '.ogg',
                   'sounds/celesta/' + filename + '.mp3'],
            volume : 0.2
        }))
        clav.push(new Howl({
            src : ['sounds/clav/' + filename + '.ogg',
                   'sounds/clav/' + filename + '.mp3'],
            volume : 0.2
        }))
    }

    // load swell sounds
    for (let i = 1; i <= 3; i++) {
        swells.push(new Howl({
            src : ['sounds/swells/swell' + i + '.ogg',
                   'sounds/swells/swell' + i + '.mp3'],
            volume : 1
        }))
    }
}

export function playSound(size, type, pan = 0, calcPanFromPitch = false) {
    // pan : (L) -1 <= pan <= 1 (R)
    const max_pitch = 100.0;
    const log_used = 1.0715307808111486871978099;
    const pitch = 100 - Math.min(max_pitch, Math.log(size + log_used) / Math.log(log_used));
    const arrayLength = Object.keys(celesta).length;
    let index = Math.floor(pitch / 100.0 * arrayLength);
    const fuzz = Math.floor(Math.random() * 4) - 2;
    index += fuzz;
    index = Math.min(arrayLength - 1, index);
    index = Math.max(1, index);
    if (calcPanFromPitch) {
        // console.debug("Calculating pan from pitch");
        pan = index * 2 / arrayLength - 1 ;
    // } else {
    //     console.debug("Pitch pre-calculated");
    }

    // console.debug("Size: " + Math.round(size) + ", index : " + index + ", Pan: " + pan + ", array length: " + arrayLength);
    if (type === 'add') {
        celesta[index].stereo(pan).play();
    } else {
        clav[index].stereo(pan).play();
    }
}

export function playRandomSwell() {
    var index = Math.round(Math.random() * (swells.length - 1));
    swells[index].play();
}
