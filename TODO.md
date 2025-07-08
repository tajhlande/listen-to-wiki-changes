# Tasks To-do

## core functionality and usability
* maybe sort the wiki list and languages 
* check color scheme for color deficiency legibility

## bugs
* make mobile responsive
* when window/tab doesn't have focus or is not visible, circles are created but not deleted, leading to lag
  * this appears to be the designed behavior for d3, per comments by Mike Bostock on filed issues
  * next best option is to stop creating circles when the window/tab is not visible, with the same logic as d3
  
## feature matches to original
* add link to user page in recent changes
* maybe: change color scheme back to original: Green circles show edits from unregistered contributors, and purple 
  circles mark edits performed by automated bots.
* add toggles to hide: 
  * article titles
  * new user announcements
* add ability to filter for edits with a hashtag in the edit summary
* link to diffs instead of pages
* consider identifying unregistered users (or temp accounts)
* cap amount of currently playing sounds

## enhancements
* give bot edits a different fill pattern
* show total counts for wikis, languages, and types on tab labels
* i18n for UI text
* render using WebGL for better performance. some options:
  * [three.js](https://threejs.org/)
  * [d3fc](https://github.com/d3fc/d3fc) 
  * [regl](https://regl-project.github.io/regl/)

## blocked ideas
* see if reverts are specifically tagged, so they could get a distinct look
  * NOTE they are not tagged as reverts
* include events where a Wikidata edit triggers a page reparse
  * NOTE these events aren't sent by the event stream SSE because in the judgment of the Data Engineering team,
    they are too numerous and would be noisy. Maybe

## developer doc and deployment readiness
* test on 
  * macos chrome ✅
  * ios ✅
  * android chrome browser ❌
* prod deployment ✅
* make a logo that can be the fav icon
