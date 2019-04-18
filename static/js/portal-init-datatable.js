$(document).ready(function() {
	$('[data-toggle="tooltip"]').tooltip();

    if ($('.results-table').DataTable) {
        $('.results-table').DataTable({
            ordering: true,
            paging: true,
            searching: false,
            order: [[ 5, "desc" ]],
            columnDefs: [{orderable: false, targets: 6}]
        });
    }
});