function addFilter({ filterEl, attributeName }) {
  $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
    const selectedValue = filterEl.value;
    const row = settings.aoData[dataIndex].nTr;
    const rowValue = row.getAttribute(attributeName);

    return !selectedValue || rowValue === selectedValue;
  });

  filterEl.addEventListener('change', () => {
    // Redraw all tables on filter change
    $('.dataTable').each(function () {
      $(this).DataTable().draw();
    });
  });
}


function addToggleFilter({ toggleSelector, attributeName, tableSelector = null, mode = 'any' }) {
  $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
    // If scoping to a specific table, skip other tables
    if (tableSelector) {
      const tableEl = settings.nTable;
      if (!tableEl || ('#' + tableEl.id) !== tableSelector) return true;
    }

    const toggles = document.querySelectorAll(toggleSelector);
    if (!toggles || toggles.length === 0) return true;

    const selectedValues = Array.from(toggles)
      .filter(el => el.checked)
      .map(el => el.value);

    // No toggles selected => no filtering
    if (selectedValues.length === 0) return true;

    const row = settings.aoData[dataIndex].nTr;
    const raw = row.getAttribute(attributeName) || '';
    const rowValues = raw.split(',').map(s => s.trim()).filter(Boolean);

    if (mode === 'all') {
      // Must contain ALL selected orgs
      return selectedValues.every(v => rowValues.includes(v));
    }

    // Default: must contain ANY selected org
    return selectedValues.some(v => rowValues.includes(v));
  });

  // Redraw all tables on toggle change (matches addFilter style)
  document.querySelectorAll(toggleSelector).forEach(el => {
    el.addEventListener('change', () => {
      $('.dataTable').each(function () {
        $(this).DataTable().draw();
      });
    });
  });
}


function initTable(selector) {
  const el = document.querySelector(selector);
  if (el) {
    $(el).DataTable({
      autoWidth: false,
      classes: { table: 'table table-striped' },
      layout: {
        topStart: 'search',
        topEnd: 'pageLength',
        bottomStart: 'info',
        bottomEnd: 'paging'
      },
      // Hide the sort arrows in column headers; clicking a header still sorts.
      ordering: { indicators: false },
      pageLength: 10,
      responsive: true,
      // Tables can relabel their filter box, e.g. to distinguish it from the search page's main search box.
      language: el.dataset.searchLabel ? { search: el.dataset.searchLabel } : {}
    });
  }
}

// Mirrors services.term_rank: 0 exact id/name, 1 id/name prefix, 2 id/name substring, 3 description only.
// Unnamed terms (e.g. indications) skip the substring tier, so "braf" doesn't match "ind:fda:braftovi:0" by id.
function rankTerm(term, query) {
  const keys = [term.id, term.name].map(value => (value || '').toLowerCase());
  if (keys.includes(query)) return 0;
  if (keys.some(key => key.startsWith(query))) return 1;
  if (term.name && keys.some(key => key.includes(query))) return 2;
  if ((term.description || '').toLowerCase().includes(query)) return 3;
  return null;
}


// Appends `text` to `parent`, wrapping the first case-insensitive match of `query` in <mark>.
function appendHighlighted(parent, text, query) {
  const index = text.toLowerCase().indexOf(query);
  if (index === -1) {
    parent.append(text);
    return;
  }
  const mark = document.createElement('mark');
  mark.textContent = text.slice(index, index + query.length);
  parent.append(text.slice(0, index), mark, text.slice(index + query.length));
}


// Returns ~`width` characters of `text` centered on the first match of `query`.
function snippet(text, query, width = 120) {
  const index = text.toLowerCase().indexOf(query);
  let start = Math.max(0, index - Math.floor((width - query.length) / 2));
  // Start on a word boundary, as long as it doesn't skip past the match.
  const space = text.indexOf(' ', start);
  if (start > 0 && space !== -1 && space < index) start = space + 1;
  const end = Math.min(text.length, start + width);
  return (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
}


function initTermSearch({ inputId, resultsId, dataId, maxNameMatches = 10, maxDescriptionMatches = 5 }) {
  const input = document.getElementById(inputId);
  const results = document.getElementById(resultsId);
  const data = document.getElementById(dataId);
  if (!input || !results || !data) return;

  const terms = JSON.parse(data.textContent);
  const searchUrl = input.form.getAttribute('action');
  let options = [];
  let activeIndex = -1;

  function close() {
    results.hidden = true;
    results.replaceChildren();
    input.setAttribute('aria-expanded', 'false');
    options = [];
    activeIndex = -1;
  }

  function setActive(index) {
    options.forEach((option, i) => {
      option.classList.toggle('active', i === index);
      option.setAttribute('aria-selected', i === index ? 'true' : 'false');
    });
    activeIndex = index;
    if (index >= 0) {
      options[index].scrollIntoView({ block: 'nearest' });
      input.setAttribute('aria-activedescendant', options[index].id);
    } else {
      input.removeAttribute('aria-activedescendant');
    }
  }

  function buildOption(term, query) {
    const item = document.createElement('li');
    item.className = 'list-group-item list-group-item-action';

    const header = document.createElement('div');
    header.className = 'd-flex justify-content-between align-items-start gap-2';
    const label = document.createElement('span');
    appendHighlighted(label, term.name || term.label, query);
    // Description matches show the record id, since the matched text alone doesn't say which record it is.
    const badge = document.createElement('span');
    badge.className = 'badge text-bg-secondary flex-shrink-0';
    badge.textContent = term.rank === 3 ? term.id : term.type;
    header.append(label, badge);
    item.append(header);

    if (term.rank === 3 && term.name) {
      const detail = document.createElement('div');
      detail.className = 'small text-muted';
      appendHighlighted(detail, snippet(term.description, query), query);
      item.append(detail);
    } else if (term.rank < 3 && term.name && term.id.toLowerCase().includes(query)) {
      const detail = document.createElement('div');
      detail.className = 'small text-muted';
      appendHighlighted(detail, term.id, query);
      item.append(detail);
    } else if (term.rank === 3) {
      // Unnamed terms (e.g. indications) show the matching part of their description as the label.
      label.replaceChildren();
      appendHighlighted(label, snippet(term.description, query), query);
    }

    return addOption(item, term.url);
  }

  // Registers a keyboard-selectable option that opens `url`. Hovering only styles the option (via CSS), so the
  // Enter key opens an option only after it is chosen with the arrow keys.
  function addOption(item, url) {
    item.setAttribute('role', 'option');
    item.id = `${resultsId}-${options.length}`;
    item.addEventListener('mousedown', event => {
      // mousedown fires before the input's blur, which would otherwise close the list first.
      event.preventDefault();
      window.location.href = url;
    });
    options.push(item);
    return item;
  }

  function render() {
    const query = input.value.trim().toLowerCase();
    if (query.length < 2) {
      close();
      return;
    }

    const matches = terms
      .map(term => ({ ...term, rank: rankTerm(term, query) }))
      .filter(term => term.rank !== null)
      .sort((a, b) => a.rank - b.rank || a.label.localeCompare(b.label));
    const nameMatches = matches.filter(term => term.rank < 3).slice(0, maxNameMatches);
    const descriptionMatches = matches.filter(term => term.rank === 3).slice(0, maxDescriptionMatches);

    results.replaceChildren();
    options = [];
    activeIndex = -1;

    nameMatches.forEach(term => results.append(buildOption(term, query)));
    if (descriptionMatches.length > 0) {
      const divider = document.createElement('li');
      divider.className = 'list-group-item term-search-divider text-muted';
      divider.textContent = 'Mentioned in';
      results.append(divider);
      descriptionMatches.forEach(term => results.append(buildOption(term, query)));
    }

    const footer = document.createElement('li');
    if (matches.length === 0) {
      footer.className = 'list-group-item term-search-divider text-muted';
      footer.textContent = 'No matches';
    } else {
      footer.className = 'list-group-item list-group-item-action term-search-all';
      footer.textContent = `See all ${matches.length} result${matches.length === 1 ? '' : 's'}`;
      addOption(footer, `${searchUrl}?q=${encodeURIComponent(input.value.trim())}`);
    }
    results.append(footer);

    results.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  input.addEventListener('input', render);
  input.addEventListener('focus', render);
  input.addEventListener('blur', close);
  input.addEventListener('keydown', event => {
    if (results.hidden) return;
    if (event.key === 'ArrowDown' && options.length > 0) {
      event.preventDefault();
      setActive((activeIndex + 1) % options.length);
    } else if (event.key === 'ArrowUp' && options.length > 0) {
      event.preventDefault();
      setActive(activeIndex <= 0 ? options.length - 1 : activeIndex - 1);
    } else if (event.key === 'Enter' && activeIndex >= 0) {
      // A highlighted suggestion opens directly; otherwise Enter submits the form to /search.
      event.preventDefault();
      options[activeIndex].dispatchEvent(new MouseEvent('mousedown'));
    } else if (event.key === 'Escape') {
      close();
    }
  });
}


document.addEventListener('DOMContentLoaded', function () {
  initTermSearch({
    inputId: 'term-search',
    resultsId: 'term-search-results',
    dataId: 'term-search-data'
  });

  // Shared filters
  const organizationFilter = document.getElementById('organizationFilter');
  if (organizationFilter) {
    addFilter({
      filterEl: organizationFilter,
      attributeName: 'data-organization'
    });
  }

  const orgToggles = document.querySelectorAll('.org-toggle');
  if (orgToggles && orgToggles.length > 0) {
    addToggleFilter({
      toggleSelector: '.org-toggle',
      attributeName: 'data-orgs',
      tableSelector: '#propositions-therapeutic-response-table-result', 
      mode: 'any'
    });
  }

  const orgClear = document.getElementById('org-clear');
  if (orgClear) {
    orgClear.addEventListener('click', () => {
      document.querySelectorAll('.org-toggle').forEach(el => (el.checked = false));
      $('.dataTable').each(function () {
        $(this).DataTable().draw();
      });
    });
  }

  const conceptFilter = document.getElementById('conceptFilter');
  if (conceptFilter) {
    addFilter({
      filterEl: conceptFilter,
      attributeName: 'data-concept'
    });
  }

  const biomarkerTypeFilter = document.getElementById('biomarkerTypeFilter');
  if (biomarkerTypeFilter) {
    addFilter({
      filterEl: biomarkerTypeFilter,
      attributeName: 'data-biomarkerType'
    });
  }

  const therapyTypeFilter = document.getElementById('therapyTypeFilter');
  if (therapyTypeFilter) {
    addFilter({
      filterEl: therapyTypeFilter,
      attributeName: 'data-therapyType'
    });
  }

  // Table selectors
  const tableSelectors = [
    '#biomarkers-table-result',
    '#diseases-table-result',
    '#documents-table-result',
    '#genes-table-result',
    '#indications-table-result',
    '#propositions-therapeutic-response-table-result',
    '#search-table-result',
    '#statements-table-result',
    '#therapies-table-result'
  ];

  tableSelectors.forEach(initTable);
});
