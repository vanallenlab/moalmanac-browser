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
      pageLength: 10,
      responsive: true
    });
  }
}

document.addEventListener('DOMContentLoaded', function () {
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
