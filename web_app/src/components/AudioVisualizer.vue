<script setup>
import { onMounted, watch } from "vue";
import * as d3 from "d3";
import {getWikiCodes, useRecentChange} from "../composition.js";
import { FixedLengthQueue, calc_rate_in_epm } from "../rate_measure.js";
import {loadSounds, calculateSize, playSound, playRandomSwell} from "../audio.js";

loadSounds();

const { recentChange } = useRecentChange();

const width = 1000;
const height = 600;
// TODO: Move these options out of this file
const max_life = 60000,
  DEFAULT_LANG = "en";

const body_background_color = "#f8f8f8",
  body_text_color = "#000",
  svg_background_color = "#1c2733",
  svg_text_color = "#fff",
  newuser_box_color = "rgb(41, 128, 185)",
  bot_color = "rgb(155, 89, 182)",
  anon_color = "rgb(46, 204, 113)",
  grow_color = "#2686cf", //"rgb(38, 134, 207)", // rgb(0, 144, 255)
  shrink_color = "#de9332" ,  //"rgb(222, 147, 50)", // "rgb(255, 144, 0)",
  new_user_color = "rgb(205, 40, 214)",
  new_page_color = "rgb(145, 212, 29)",
  circle_middle_color = "rgba(255, 255, 255, 0.5)",
  sound_totals = 51,
  total_edits = 0;

let silent = false;

const wikiCodeMap  = new Map(getWikiCodes().map(item => [item.wikiCode, item]));

const MAX_RATE_QUEUE_SIZE = 30;
const MAX_EVENT_AGE_FOR_RATE = 10 * 1000; // in milliseconds
const UPDATE_RATE_EVERY = 3 * 1000; // in milliseconds
const rateMeasureQueue = new FixedLengthQueue(MAX_RATE_QUEUE_SIZE);
let eventsPerMinute = 0.0;
let epm_text = false;
let overlay_group = {};
let circles_container = {};
let epm_container = {};

function new_user_action(data, svg_area) {
  let wikiName = wikiCodeMap.get(data.code).displayName;
  let messages = ['Welcome ' + data.user + ', ' + wikiName + '\'s newest user!',
                  wikiName + ' has a new user, ' + data.user + '! Welcome!',
                  'Welcome, ' + data.user + ' has joined ' + wikiName + '!'];
  let message = Math.round(Math.random() * (messages.length - 1));

  let user_group = svg_area.append('g');

  let user_container = user_group.append('a')
      .attr('xlink:href', data.title_url)
      .attr('target', '_blank');

  user_group.transition()
      .delay(7000)
      .remove();

  user_container.transition()
      .delay(4000)
      .style('opacity', 0)
      .duration(3000);

  user_container.append('rect')
      .attr('opacity', 0)
      .transition()
      .delay(100)
      .duration(3000)
      .attr('opacity', 1)
      .attr('fill', newuser_box_color)
      .attr('width', width)
      .attr('height', 35);

  let y = width / 2;

  user_container.append('text')
      .classed('newuser-label', true)
      .attr('transform', 'translate(' + y +', 25)')
      .transition()
      .delay(1500)
      .duration(1000)
      .text(messages[message])
      .attr('text-anchor', 'middle');

}

function update_epm_display(epm, svg_area) {
  if (!epm_text) {
    epm_container = svg_area.append('g')
        .attr('transform', 'translate(0, ' + (height - 25) + ')');

    var epm_box = epm_container.append('rect')
        .attr('fill', newuser_box_color)
        .attr('opacity', 0.5)
        .attr('width', 140)
        .attr('height', 25);

    epm_text = epm_container.append('text')
        .classed('newuser-label', true)
        .attr('transform', 'translate(5, 18)')
        .attr('opacity', 1)
        .style('font-size', '.8em')
        .text(epm + ' events per minute');

  } else if (epm_text.text) {
    epm_text.text(epm + ' events per minute');
  }
}


onMounted(() => {
  let svg = d3
    .select("#area")
    .append("svg")
    .attr("preserveAspectRatio", "xMinYMin meet")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .classed("svg-content", true)
    .style("background-color", "#1c2733");
  circles_container = svg.append('g');
  overlay_group = svg.append('g');

  // update the events per minute measurement once per every
  let rateMeasureInterval = setInterval(() =>{
      let currentTime = Date.now();
      // console.debug('Queue length (' + rateMeasureQueue.size + ') and max age in s (' +
      //     (rateMeasureQueue.isEmpty() ? 'undefined' :
      //         (currentTime - (rateMeasureQueue.peek()))/1000) + ') for calc:')
      eventsPerMinute = calc_rate_in_epm(rateMeasureQueue, currentTime, MAX_EVENT_AGE_FOR_RATE);
      // console.debug('Events per minute: ' + eventsPerMinute)
      update_epm_display(eventsPerMinute, overlay_group)
    },UPDATE_RATE_EVERY);

  watch(recentChange, () => {
    const data = recentChange.value.data;
    // console.log(data)

    const isAddingContent = data.change_in_length > 0;

    // calculate the 'magnitude' of both the audio and visuals
    const [origSize, scaledSize] = calculateSize(recentChange.value.data);
    const x = Math.random() * (width - scaledSize) + scaledSize;
    const y = Math.random() * (height - scaledSize) + scaledSize;
    if (data.event_type === 'new_user') {
      playRandomSwell();
      new_user_action(data, svg)
    } else {
      // play audio
      const pan = x * 2 / width - 1;
      if (origSize > 0) {
        playSound(scaledSize, 'add', pan)
      } else {
        playSound(scaledSize, 'sub', pan)
      }
    }

    // track the new event for rate measurement
    let currentTimestamp = Date.now();
    // console.debug('Enqueueing timestamp: ' + currentTimestamp);
    rateMeasureQueue.enqueue(currentTimestamp);

    // draw circle
    let label_text = data.title;
    let no_label = true;
    let type = data.event_type;
    let starting_opacity = silent ? 0.2 : 0.8;

    const circle_id = "d" + ((Math.random() * 100000) | 0);


    let circle_color = isAddingContent ? grow_color : shrink_color;
    if (data.event_type === 'new_user') circle_color = new_user_color;
    if (data.event_type === 'new_page') circle_color = new_page_color

    const circle_group = circles_container
      .append("g")
      .attr("transform", "translate(" + x + ", " + y + ")")
      .attr("fill", circle_middle_color)
      .style("opacity", starting_opacity);

    const ring = circle_group
      .append("circle")
      .attr("r", scaledSize + 20)
      .attr("stroke", "none")
      .transition()
      .attr("r", scaledSize + 40)
      .style("opacity", 0)
      .ease(Math.sqrt)
      .duration(2500)
      .remove();

    const circle_container = circle_group
      .append("a")
      .attr("xlink:href", data.title_url)
      .attr("target", "_blank")
      .attr("fill", svg_text_color);

    const circle = circle_container
      .append("circle")
      .classed("visualizer-circle", true)
      .classed(type, true)
      .attr("r", scaledSize)
      .transition()
      .duration(max_life)
      .attr("fill", circle_color)
      .style("opacity", 0)
        .attr("opacity", 0)
      .on("end", function () {
        circle_group.remove();
      })
      .remove();

    circle_container
      .append("text")
      .text(label_text)
      .classed("article-label", true)
      .attr("text-anchor", "middle");

    circle_container.append('text')
        .text(label_text)
        .classed('article-label', true)
        .attr('text-anchor', 'middle')
        .style('opacity', 1)
        .transition()
        .delay(1000)
        .style('opacity', 0)
        .duration(2000)
        //.each('end', function() { no_label = true; })
        .remove();
  });
});
</script>

<template>
  <div id="area" class="anchor-target"></div>
</template>
<style>

#area {
  padding-top: 48px;
}

.article-label {
  opacity: 0;
  transition: opacity 1s;
  will-change: opacity;
}

.article-label:hover,
.visualizer-circle:hover+.article-label {
  opacity: 1;
}

.edit {
  transition: fill 1s;
  /* fill: var(--background-color-progressive); */
}

.edit:hover {
  /*fill: var(--background-color-progressive--hover);*/
}
</style>
