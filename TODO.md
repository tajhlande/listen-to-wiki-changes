# Tasks To-do

## core functionality and usability
* fix initial circles to show title that fades with ring 
* add new user welcome banner across the top, "Welcome XXX to YYYpedia!"
  * change language in recent changes log to match
* fix layout issues
  * Get rid of extra padding at the top under the title
  * bound the wiki selector tab contents inside a scrollable pane for the very long list of wikis
  * maybe make the wiki list 
* fix missing shadow styling of article titles
* check color scheme for color deficiency legibility
* figure out why phantom subscriptions and duplicate events happen

## feature matches to original
* add link to new user welcome banner to their talk page.
* add link to user page in recent changes
* add language for "added / removed bytes" in recent changes long
* maybe: change color scheme back to original: Green circles show edits from unregistered contributors, and purple circles mark edits performed by automated bots.
* add changes-per-minute metric in corner
* add volume slider
* add toggles to hide: 
  * article titles
  * new user announcements
  * recent changes console
  * graphics for background listening
* add ability to filter for edits with a hashtag in the edit summary
* link to diffs instead of pages
* consider identifying unregistered users (or temp accounts)
* stereo pan the sounds left or right based on screen position of circle

## enhancements
* see if reverts are specifically tagged, so they could get a distinct look
* give bot edits a different fill pattern
* show total counts for wikis, languages, and types on tab labels
* pin header to top while scrolling down page
* tweak aspect ratio for svg, make mobile responsive
* add clear all button 

## developer doc and deployment readiness
* add developer start documentation
* add other doc
* clean up code comments 
* delete unused code and files
* test on 
  * macos chrome
  * ios
  * android chrome browser
* prod deployment 
* make a logo that can be the fav icon
