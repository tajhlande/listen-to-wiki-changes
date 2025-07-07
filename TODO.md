# Tasks To-do

## core functionality and usability
* maybe sort the wiki list and languages 
* check color scheme for color deficiency legibility

## bugs
* when window/tab doesn't have focus, circles are created but not deleted, leading to lag

## feature matches to original
* add link to user page in recent changes
* maybe: change color scheme back to original: Green circles show edits from unregistered contributors, and purple 
  circles mark edits performed by automated bots.
* add toggles to hide: 
  * article titles
  * new user announcements
  * recent changes console
  * graphics for background listening
* add ability to filter for edits with a hashtag in the edit summary
* link to diffs instead of pages
* consider identifying unregistered users (or temp accounts)
* cap amount of currently playing sounds

## enhancements
* stereo pan the sounds left or right based on screen position of circle
* give bot edits a different fill pattern
* show total counts for wikis, languages, and types on tab labels
* make mobile responsive
* i18n for UI text

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
