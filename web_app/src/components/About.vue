<script setup>

</script>

<template>
  <div class="about-box">
    <h3 id="about" class="anchor-target">About this project</h3>
    <p>
      Listen to the sound of Wikimedia's recent changes feed.
      This app visualizes and sonifies recent edits, new page creation, and new user account creation events
      from any of the hundreds of wiki instances hosted by Wikimedia, including Wikipedia, Wiktionary, Commons,
      and others.
    </p>
    <p>
      Celesta bells indicate additions and string plucks indicate subtractions.
      Pitch changes according to the size of the edit; the larger the edit, the deeper the note.
      Blue circles show edits that add content, and orange circles show edits that remove content.
      Green circles show newly created pages.
      Each circle is clickable to visit the page that was edited.
      You may see announcement banners for new users as they join the site, punctuated by a string swell.
      You can welcome him or her by clicking the banner and adding a note on their talk page.
    </p>
    <p>
      <b>Listen to Wiki Changes</b> is a refresh of a project originally built by Hatnote,
      <a target="_blank" href="http://github.com/slaporte">Stephen LaPorte</a> and
      <a href="https://github.com/mahmoud">Mahmoud Hashemi</a>.
      Updates were contributed by
      <a target="_blank" href="https://gitlab.wikimedia.org/ttaylor">Tajh Taylor</a>,
      <a target="_blank" href="https://gitlab.wikimedia.org/xcollazo">Xabriel Collazo</a>, and
      <a target="_blank" href="https://gitlab.wikimedia.org/tchin">Thomas Chin</a>.
      The original app is here: <a target="_blank" href="http://listen.hatnote.com">listen.hatnote.com</a>,
      and there is a <a target="_blank" href="http://blog.hatnote.com/post/56856315107/listen-to-wikipedia">blog post</a>
      about the original launch of the project.
      It was inspired by
      <a href="http://bitlisten.com">BitListen</a> by <a href="https://www.maxlaumeister.com/">Maximillian Laumeister</a>.
      The source code is <a href="https://gitlab.wikimedia.org/toolforge-repos/listen-to-wiki-changes">available on
      Wikimedia's Gitlab</a>
    </p>


    <p>
      This project is built using:
    </p>
    <ul>
      <li><a target="_blank" href="https://vuejs.org/">Vue.js</a></li>
      <li><a target="_blank" href="https://d3js.org">D3</a></li>
      <li><a href="https://github.com/goldfire/howler.js">HowlerJS</a></li>
      <li><a href="https://fastapi.tiangolo.com/">FastAPI</a></li>
    </ul>
  </div>

</template>

<style scoped>
.about-box {
  width: auto;
  max-width: 800px;
  margin: auto;
  margin-top: 2rem;
}
</style>
