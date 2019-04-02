$(document).ready(function() {
	$('[data-toggle="tooltip"]').tooltip();
	$('.browse-dropdown').on('change', function() { this.form.submit() })
});

if ($('.typeahead')) {
    var typeahead_features = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        prefetch: 'api/features'
    });

    $('.typeahead').typeahead({
        hint: true,
        highlight: true,
        minLength: 1,
    },
    {
        name: 'typeahead_features',
        source: typeahead_features
    });

    $('#feature-input').bind('typeahead:select', function(ev, suggestion) {
        $('#feature-input').value = suggestion;
        this.form.submit();
    });
}

$(document).ready(function(){
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
