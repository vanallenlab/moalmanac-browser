function addFilter({ filterEl, attributeName, filterKey }) {
  $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
    const selectedValue = filterEl.value;
    const row = settings.aoData[dataIndex].nTr;
    const rowValue = row.getAttribute(attributeName);

    return !selectedValue || rowValue === selectedValue;
  });

  filterEl.addEventListener('change', () => {
    // Force all tables to redraw when a shared filter changes
    $('.dataTable').DataTable().draw();
  });
}

document.addEventListener('DOMContentLoaded', function () {
  const organizationFilter = document.getElementById('organizationFilter');
  if (organizationFilter) {
    addFilter({
      filterEl: organizationFilter,
      attributeName: 'data-organization',
      filterKey: 'organization'
    });
  }

  const therapyTypeFilter = document.getElementById('therapyTypeFilter');
  if (therapyTypeFilter) {
    addFilter({
      filterEl: therapyTypeFilter,
      attributeName: 'data-therapyType',
      filterKey: 'therapyType'
    });
  }

  // Table setup
  const tableSelectors = [
    '#biomarkers-table-result',
    '#diseases-table-result',
    '#documents-table-result',
    '#genes-table-result',
    '#indications-table-result',
    '#propositions-therapeutic-response-table-result',
    '#therapies-table-result'
  ];

  tableSelectors.forEach(selector => {
    const el = document.querySelector(selector);
    if (el) {
      new DataTable(el, {
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
  });
});
