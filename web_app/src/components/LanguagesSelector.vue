<script setup>
import { CdxCheckbox, CdxSearchInput, CdxTabs, CdxTab } from "@wikimedia/codex";
import { computed, watch, ref, reactive, onMounted } from "vue";
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

// these are lists of items
const wikiCodes = reactive(getWikiCodes());
const wikiLangs = reactive(getWikiLangs());
const wikiTypes = reactive(getWikiTypes());

// decorate each of the wiki metadata objects with a "checked" property
for (let wikiCode of wikiCodes) { wikiCode['checked'] = false }
for (let wikiLang of wikiLangs) { wikiLang['checked'] = false }
for (let wikiType of wikiTypes) { wikiType['checked'] = false }

const {
  wikiCodeFilter,
  wikiLangFilter,
  wikiTypeFilter
} = useRecentChange();

var enWikiCode, deWikiCode, zhWikiCode;

// Watch every checkbox for change
wikiCodes.forEach((wikiCode) => {
  if (wikiCode.wikiCode === 'en_wikipedia') {
    enWikiCode = wikiCode;
  } else if (wikiCode.wikiCode === 'de_wikipedia') {
    deWikiCode = wikiCode;
  } else if (wikiCode.wikiCode === 'zh_wikipedia') {
    zhWikiCode = wikiCode;
  }


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

console.assert(enWikiCode != null, "enWikiCode was not found");

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

onMounted(() => {
  console.log("Adding event listener for start-listening");
  window.addEventListener('start-listening', (event) => {
    // Handle the event
    console.log('Received event to start listening');
    enWikiCode.checked = true;
    deWikiCode.checked = true;
    zhWikiCode.checked = true;
  });
});

</script>

<template>
  <div id="selector-container" class="anchor-target">
    <cdx-search-input v-model="searchInput" aria-label="Search Wiki Codes" placeholder="e.g. English" />
    <cdx-tabs class="selector-tabs" v-model:active="currentTab" :framed="true">
      <cdx-tab v-for="(tab, index) in tabsData" :key="index" :name="tab.name" :label="tab.label">
        <div v-if="currentTab === 'all'" id="wiki-codes-grid" class="selector-grid">
          <cdx-checkbox v-for="wikiCode in codesSearchResults" v-model="wikiCode.checked" :key="wikiCode.wikiCode" :ref="'cb-' + wikiCode.wikiCode">
            <span v-html="wikiCode.displayName"></span>
          </cdx-checkbox>
        </div>
        <div v-if="currentTab === 'bylang'" id="wiki-langs-grid" class="selector-grid">
          <cdx-checkbox v-for="lang in langsSearchResults" v-model="lang.checked" :key="lang.langCode" :ref="'cb-' + lang.langCode">
            <span v-html="lang.enName + ' (' + lang.localName + ')'"></span>
          </cdx-checkbox>
        </div>
        <div v-if="currentTab === 'bytype'" id="wiki-types-grid" class="selector-grid">
          <cdx-checkbox v-for="wikiType in typesSearchResults" v-model="wikiType.checked" :key="wikiType.wikiType" :ref="'cb-' + wikiType.wikiType">
            <span v-html="wikiType.wikiType"></span>
          </cdx-checkbox>
        </div>
      </cdx-tab>
    </cdx-tabs>
  </div>
</template>

<style scoped>

.selector-grid {
  margin: 0;
  padding: 1rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  max-height: 500px;
  overflow-y: auto;
}

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
