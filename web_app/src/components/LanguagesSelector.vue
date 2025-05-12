<script setup>
import { CdxCheckbox, CdxSearchInput, CdxTabs, CdxTab } from "@wikimedia/codex";
import { computed, watch, ref, reactive } from "vue";
import { useRecentChange, getWikiCodes, getWikiLangs, getWikiTypes } from "../composition.js";

const currentTab = ref("all");
const tabsData = [
  {
    name: "all",
    label: "All Sites",
  },
  {
    name: "bylang",
    label: "By Languages",
  },
  {
    name: "bytype",
    label: "By Type",
  }
];

// const groupWikisByProperty = (wikis, property) => {
//   const map = wikis.reduce((accumulator, wiki) => {
//     if (accumulator.has(wiki[property])) {
//       accumulator.get(wiki[property]).push(wiki);
//     } else {
//       accumulator.set(wiki[property], [wiki]);
//     }
//     return accumulator;
//   }, new Map());
//
//   let arr = [];
//   for (const [key, value] of map.entries()) {
//     arr.push({
//       title: key,
//       lang: key,
//       link: value[0].link,
//       checked: computed({
//         get() {
//           return value.find((wiki) => !wiki.checked) ? false : true;
//         },
//         set(newVal) {
//           value.forEach((wiki) => (wiki.checked = newVal));
//         },
//       }),
//     });
//   }
//   return arr;
// };

// these are lists now
const wikiCodes = reactive(getWikiCodes());
const wikiLangs = reactive(getWikiLangs());
const wikiTypes = reactive(getWikiTypes());

// decorate each of the wiki metadata objects with a "checked" property
for (let wikiCode of wikiCodes) { wikiCode['checked'] = false }
for (let wikiLang of wikiLangs) { wikiLang['checked'] = false }
for (let wikiType of wikiTypes) { wikiType['checked'] = false }

// const wikiCodesList = Object.keys(wikiCodes).map((key) => [key, obj[key]]);
// const wikiLangsList = Object.keys(wikiLangs).map((key) => [key, obj[key]]);
// const wikiTypesList = Object.keys(wikiTypes).map((key) => [key, obj[key]]);

// const wikisBylang = ref(groupWikisByProperty(wikis.value, "loc_lang"));
//const wikisByType = ref(groupWikisByProperty(wikis.value, "type"));

const {
  wikiCodeFilter,
  wikiLangFilter,
  wikiTypeFilter,
  recentChange
} = useRecentChange();

// Watch every checkbox for change
wikiCodes.forEach((wikiCode) => {
  watch(wikiCode, () => {
    if (wikiCode.checked) {
      wikiCodeFilter.add(wikiCode.wikiCode)
    } else {
      wikiCodeFilter.delete(wikiCode.wikiCode)
    }
    console.log("Wiki code " + JSON.stringify(wikiCode.wikiCode) + (wikiCode.checked ? " checked" : " unchecked"))
    // wikiCode.checked ? wikiCodeFilter.add(wikiCode.wiki_code) : wikiCodeFilter.delete(wikiCode.wiki_code);
  })
})

wikiLangs.forEach((wikiLang) => {
  watch(wikiLang, () => {
    wikiLang.checked ? wikiLangFilter.add(wikiLang.langCode) : wikiLangFilter.delete(wikiLang.langCode);
  })
})

wikiTypes.forEach((wikiType) => {
  watch(wikiType, () => {
    wikiType.checked ? wikiTypeFilter.add(wikiType.wikiType) : wikiTypeFilter.delete(wikiType.wikiType);
  })
})



// wikis.value.forEach((wiki) => {
//   watch(wiki, () => {
//     wiki.checked ? filter.add(wiki.link) : filter.delete(wiki.link);
//   });
// });

const searchInput = ref("");

const codesSearchData = computed(() => {
  return wikiCodes;
});

const codesSearchResults = computed(() => {
  if (searchInput.value) {
    console.log("Computing code search results for input '" + searchInput.value + "'")
    const search = searchInput.value.toLowerCase();
    let result = codesSearchData.value.filter((wikiCode) =>
      `${wikiCode.wikiCode} ${wikiCode.displayName}`.toLowerCase().includes(search)
    );
    console.log("Results size: " + result.length)
    return result
  }
  console.log("Returning full codes search dataset")
  return codesSearchData.value;
});


const langsSearchData = computed(() => {
  return wikiLangs;
});

const langsSearchResults = computed(() => {
  if (searchInput.value) {
    console.log("Computing lang search results for input '" + searchInput.value + "'")
    const search = searchInput.value.toLowerCase();
    let result = langsSearchData.value.filter((wikiLang) =>
        `${wikiLang.langCode} ${wikiLang.enName} ${wikiLang.localName}`.toLowerCase().includes(search)
    );
    console.log("Results size: " + result.length)
    return result
  }
  console.log("Returning full lang search dataset")
  return langsSearchData.value;
});


const typesSearchData = computed(() => {
  return wikiTypes;
});

const typesSearchResults = computed(() => {
  if (searchInput.value) {
    console.log("Computing type search results for input '" + searchInput.value + "'")
    const search = searchInput.value.toLowerCase();
    let result = typesSearchData.value.filter((wikiType) =>
        `${wikiType.wikiType}`.toLowerCase().includes(search)
    );
    console.log("Results size: " + result.length)
    return result
  }
  console.log("Returning full lang search dataset")
  return typesSearchData.value;
});
</script>

<template>
  <div id="selector-container">
    <cdx-search-input v-model="searchInput" aria-label="Search Wiki Codes" placeholder="e.g. English" />
    <cdx-tabs v-model:active="currentTab" :framed="true">
      <cdx-tab v-for="(tab, index) in tabsData" :key="index" :name="tab.name" :label="tab.label">
        <div v-if="currentTab === 'all'" id="wiki-codes-grid">
          <cdx-checkbox v-for="wikiCode in codesSearchResults" v-model="wikiCode.checked" :key="wikiCode.wikiCode">
            <span v-html="wikiCode.displayName"></span>
          </cdx-checkbox>
        </div>
        <div v-if="currentTab === 'bylang'" id="wiki-langs-grid">
          <cdx-checkbox v-for="lang in langsSearchResults" v-model="lang.checked" :key="lang.langCode">
            <span v-html="lang.enName + ' (' + lang.localName + ')'"></span>
          </cdx-checkbox>
        </div>
        <div v-if="currentTab === 'bytype'" id="wiki-types-grid">
          <cdx-checkbox v-for="wikiType in typesSearchResults" v-model="wikiType.checked" :key="wikiType.wikiType">
            <span v-html="wikiType.wikiType"></span>
          </cdx-checkbox>
        </div>
      </cdx-tab>
    </cdx-tabs>
  </div>
</template>

<style scoped>
#language-grid {
  margin: 0 auto;
  margin-top: 1rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

#selector-container {
  width: auto;
  max-width: 800px;
  margin: auto;
  margin-bottom: 1rem;
}
</style>
