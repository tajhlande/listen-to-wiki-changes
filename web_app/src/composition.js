import {reactive, ref, shallowReactive, toRaw, watch} from "vue";

const domParser = new DOMParser();
//const baseUrl = location.origin; //+ import.meta.env.BASE_URL;
console.log("Location.origin: " + location.origin);
console.log("Import.meta.env.BASE_URL: " + import.meta.env.BASE_URL);

console.log("App mode: " + import.meta.env.MODE)
const baseUrl = (import.meta.env.MODE === 'development') ? "http://localhost:8000" : location.origin;
// const baseUrl = "http://localhost:8000";
console.log('Base app URL: ' + baseUrl);

/*
Examples of each:
Wiki Code objects
{"wiki_code":"commons","display_name":"Commons Wiki"}
{"wiki_code":"de_wikipedia","display_name":"German Wikipedia"}

Wiki Language objects
{"lang_code":"en","en_name":"English","local_name":"English"}
{"lang_code":"zh","en_name":"Chinese","local_name":"中文"}

Wiki type objects
{"wiki_type":"special"}
{"wiki_type":"wikipedia"}
 */
const wikiCodes = await fetch(baseUrl + "/api/wiki_codes")
    .then((res) => res.json());
const wikiLangs = await fetch(baseUrl + "/api/languages")
    .then((res) => res.json());
const wikiTypes = await fetch(baseUrl + "/api/types")
    .then((res) => res.json());


console.log("First 10 wiki codes (" + wikiCodes.length + " total): " + JSON.stringify(wikiCodes.slice(0, 10)));
console.log("First 10 wiki langs (" + wikiLangs.length + " total): " + JSON.stringify(wikiLangs.slice(0, 10)));
console.log("First 10 wiki types (" + wikiTypes.length + " total): " + JSON.stringify(wikiTypes.slice(0, 10)));
// console.dir(wikiCodes)
// console.dir(wikiLangs)
// console.dir(wikiTypes)
// console.log("First wiki code object: " + JSON.stringify(wikiCodes[0]))

export const getWikiCodes = () => wikiCodes.map((item) => reactive(item));
export const getWikiLangs = () => wikiLangs.map((item) => reactive(item));
export const getWikiTypes = () => wikiTypes.map((item) => reactive(item));

const wikiCodeFilter = shallowReactive(new Set());
const wikiLangFilter = shallowReactive(new Set());
const wikiTypeFilter = shallowReactive(new Set());
const recentChange = ref();
const worker = new SharedWorker(new URL("./relay_client_shared_worker.js", import.meta.url));

worker.port.onmessage = (e) => {
  recentChange.value = e;
};

watch([wikiCodeFilter, wikiLangFilter, wikiTypeFilter], () => {
  worker.port.postMessage({
    apiUrl: baseUrl + "/api/events",
    wikiCodes: Array.from(toRaw(wikiCodeFilter)),
    wikiLangs: Array.from(toRaw(wikiLangFilter)),
    wikiTypes: Array.from(toRaw(wikiTypeFilter)),
  })
  // worker.port.postMessage(toRaw(filter));
});

/**
 * @typedef {UseRecentChangeReturn} UseRecentChangeReturn
 * @property {ShallowReactive<Set<String>>} wikiCodeFilter - The wiki code filter used for recent changes
 * @property {ShallowReactive<Set<String>>} wikiTypeFilter - The wiki type filter used for recent changes
 * @property {ShallowReactive<Set<String>>} wikiLangFilter - The wiki lang filter used for recent changes
 * @property {Ref<MessageEvent<any>>} recentChange - The most recent change event
 *
 * @returns {UseRecentChangeReturn} UseRecentChangeReturn
 */
export const useRecentChange = () => ({
  wikiCodeFilter,
  wikiTypeFilter,
  wikiLangFilter,
  recentChange,
});
