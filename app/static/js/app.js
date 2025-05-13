document.addEventListener('DOMContentLoaded', function () {
  // DOCUMENTS TABLE SETUP
  const documentsTableEl = document.querySelector('#documents-table-result');
  const organizationFilter = document.getElementById('organizationFilter');
  if (documentsTableEl && organizationFilter) {
    // Custom filter function
    $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
      const selectedOrganization = organizationFilter.value;
      const row = settings.aoData[dataIndex].nTr;
      const rowOrganization = row.getAttribute('data-organization');

      return !selectedOrganization || rowOrganization === selectedOrganization;
    });
    const documentsTable = new DataTable(documentsTableEl, {
      autoWidth: false,
      classes: {
        table: 'table table-striped'
      },
      layout: {
        topStart: 'search',
        topEnd: 'pageLength',
        bottomStart: 'info',
        bottomEnd: 'paging'
      },
      pageLength: 10,
      responsive: true
    });
    organizationFilter.addEventListener('change', () => documentsTable.draw());
  }

  // BIOMARKERS TABLE SETUP
  const biomarkersTableEl = document.querySelector('#biomarkers-table-result');
  const biomarkerTypeFilter = document.getElementById('biomarkerTypeFilter');
  if (biomarkersTableEl && biomarkerTypeFilter) {
    $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
      const selectedBiomarkerType = biomarkerTypeFilter.value;
      const row = settings.aoData[dataIndex].nTr;
      const rowBiomarkerType = row.getAttribute('data-biomarkerType');

      return !selectedBiomarkerType || rowBiomarkerType === selectedBiomarkerType;
    });
    const biomarkersTable = new DataTable(biomarkersTableEl, {
      autoWidth: false,
      classes: {
        table: 'table table-striped'
      },
      layout: {
        topStart: 'search',
        topEnd: 'pageLength',
        bottomStart: 'info',
        bottomEnd: 'paging'
      },
      pageLength: 10,
      responsive: true
    });
    biomarkerTypeFilter.addEventListener('change',  () => biomarkersTable.draw());
  }

  // DISEASES TABLE SETUP
  const diseasesTableEl = document.querySelector('#diseases-table-result');
  if (diseasesTableEl) {
    new DataTable(diseasesTableEl, {
      autoWidth: false,
      classes: {
        table: 'table table-striped'
      },
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

  // GENES TABLE SETUP
  const genesTableEl = document.querySelector('#genes-table-result');
  if (genesTableEl) {
    new DataTable(genesTableEl, {
      autoWidth: false,
      classes: {
        table: 'table table-striped'
      },
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

  // THERAPIES TABLE SETUP
  const therapiesTableEl = document.querySelector('#therapies-table-result');
  const therapyTypeFilter = document.getElementById('therapyTypeFilter');
  if (therapiesTableEl && therapyTypeFilter) {
    $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
      const selectedTherapyType = therapyTypeFilter.value;
      const row = settings.aoData[dataIndex].nTr;
      const rowTherapyType = row.getAttribute('data-therapyType');

      return !selectedTherapyType || rowTherapyType === selectedTherapyType;
    });
    const therapiesTable = new DataTable(therapiesTableEl, {
      autoWidth: false,
      classes: {
        table: 'table table-striped'
      },
      layout: {
        topStart: 'search',
        topEnd: 'pageLength',
        bottomStart: 'info',
        bottomEnd: 'paging'
      },
      pageLength: 10,
      responsive: true
    });
    therapyTypeFilter.addEventListener('change',  () => therapiesTable.draw());
  }
});
