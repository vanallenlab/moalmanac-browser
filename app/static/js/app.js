document.addEventListener('DOMContentLoaded', function () {
  const organizationFilter = document.getElementById('organizationFilter');

  // Custom filter function
  $.fn.dataTable.ext.search.push(function (settings, data, dataIndex, rowData, counter) {
    const row = settings.aoData[dataIndex].nTr;
    const rowOrganization = row.getAttribute('data-organization');

    const selectedOrganization = organizationFilter.value;

    return !selectedOrganization|| rowOrganization === selectedOrganization;
  });

  const table = new DataTable('#table-result', {
    layout: {
      topStart: 'search',
      topEnd: 'pageLength',
      bottomStart: 'info',
      bottomEnd: 'paging'
    },
    classes: {
      table: 'table table-striped'
    },
    responsive: true,
    autoWidth: false
  });

  // Re-filter table when dropdowns change
  [organizationFilter].forEach(el =>
    el.addEventListener('change', () => table.draw())
  );
});
