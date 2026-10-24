/* Highlight text nodes only: preserve links, attributes and event handlers. */
(function (root) {
  'use strict';
  function clear(section) {
    section.querySelectorAll('mark[data-r3-search]').forEach(mark => mark.replaceWith(section.ownerDocument.createTextNode(mark.textContent)));
    section.normalize();
  }
  function highlight(section, query) {
    clear(section); if (!query) return 0;
    const doc = section.ownerDocument, walker = doc.createTreeWalker(section, 4), nodes = [];
    let text;
    while ((text = walker.nextNode())) {
      if (!text.parentElement?.closest('script,style,mark')) nodes.push(text);
    }
    const regex = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'); let count = 0;
    for (const node of nodes) {
      const value = node.nodeValue; regex.lastIndex = 0;
      const matches = [...value.matchAll(regex)]; if (!matches.length) continue;
      const fragment = doc.createDocumentFragment(); let start = 0;
      for (const match of matches) {
        fragment.append(doc.createTextNode(value.slice(start, match.index)));
        const mark = doc.createElement('mark'); mark.setAttribute('data-r3-search', ''); mark.textContent = match[0]; fragment.append(mark);
        start = match.index + match[0].length; count++;
      }
      fragment.append(doc.createTextNode(value.slice(start))); node.replaceWith(fragment);
    }
    return count;
  }
  const api = {clear, highlight};
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.R3TextSearch = api;
})(typeof window !== 'undefined' ? window : globalThis);
