$(document).ready(function() {
	$('[data-toggle="tooltip"]').tooltip();
	$('.browse-dropdown').on('change', function() { this.form.submit() })

    if ($('.results-table').DataTable) {
        $('.results-table').DataTable({
            ordering: true,
            paging: true,
            searching: false,
            "order": [[ 0, "desc" ]],
            "columnDefs": [{
                "targets": [ 0 ],
                "visible": false
            }]
        });
    }
});
