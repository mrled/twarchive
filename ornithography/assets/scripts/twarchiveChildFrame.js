/* JavaScript inside each child frame (requires twarchiveCommon.js)
 *
 * This is referenced from layouts/partials/twarchive/sigle.tweet.html,
 * which also sets a const tweetId.
 */

/* We use a global variable (attached to the window object) for a resize observer
 */
window.twarchiveResizeObserver = null;

/* Ask the parent frame to log a message for us.
 * console.log() here doesn't show up unless inspecting this frame,
 * so we pass messages to the parent.
 */
function twarchiveMessageLogEventToParent(level, logMessage) {
  const prefix = `twarchiveMessageLogEventToParent for tweet '${tweetId}' instance '${tweetInstance}'`
  const eventMessage = {
    twarchiveEvent: "twarchive-child-frame-log",
    level,
    message: `${prefix}: ${logMessage}`,
  };
  window.parent.postMessage(eventMessage, "*");
}

/* Message parent frame our size
 */
function twarchiveMessageSizeToParent(tweetId) {
  const w = window.innerWidth;
  const h = window.innerHeight;
  const msg = {twarchiveEvent: "twarchive-resize", tweetId, w, h};
  twarchiveMessageLogEventToParent("log", `Messaging parent window: ${JSON.stringify(msg)}`)
  window.parent.postMessage(msg, "*");
}

/* Start observation of the document element with a resize observer
 */
function twarchiveResizeObservationStart() {
  if (!window.twarchiveResizeObserver) {
    window.twarchiveResizeObserver = new ResizeObserver(e => twarchiveMessageSizeToParent(tweetId));
  }
  window.twarchiveResizeObserver.observe(document.documentElement);
}

/* Stop observation of the document element with out resize observer
 */
function twarchiveResizeObservationStop() {
  if (window.twarchiveResizeObserver) {
    window.twarchiveResizeObserver.unobserve(document.documentElement);
  }
}

/* Display explanation text for a twarchive tweet
 */
function twarchiveToggleTweetExplanation(button, tweetId) {
  const expl = button.parentElement.getElementsByClassName('twarchive-about-explanation')[0];

  // We must stop the resize observer before changing the display style (which changes document length).
  // If we don't, the resize observer fires dozens of times during the transition.
  // (Why is there a transition period and it's not instant? I'm not sure.)
  twarchiveResizeObservationStop();
  if (expl.style.display === 'none') {
    expl.style.display = 'block';
  } else {
    expl.style.display = 'none';
  }
  twarchiveResizeObservationStart();

  twarchiveMessageSizeToParent(tweetId);
}

/* Handle data URIs
 */
function twarchiveHandleDataUri(dataUri) {
  if (window == window.top) {
    // If this page is the top frame, we need display the image ourselves
    window.location.hash = `?twarchive-datauri#${dataUri}`;
    window.location.href = `${window.location.href}?twarchive-datauri#${dataUri}`;
    twarchiveMessageLogEventToParent("log", `Setting window.location.href to ${window.location.href}`)
    twarchiveDisplayDataUri();
  } else {
    // If we are in an iframe, we should tell our parent to display the image
    const msg = {twarchiveEvent: "twarchive-display-data-uri", dataUri};
    window.parent.postMessage(msg, "*");
  }
}