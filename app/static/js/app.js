document.addEventListener('DOMContentLoaded', function () {
  new DataTable('#table-result', {
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
});
