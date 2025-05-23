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
    '#therapies-table-result'
  ];

  tableSelectors.forEach(initTable);
});
