$(document).ready(function() {
	$('[data-toggle="tooltip"]').tooltip();
	$('.browse-dropdown').on('change', function() { this.form.submit() })
});

if ($('.typeahead')) {
    const typeahead_features = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        prefetch: 'api/features'
    });

    const typeahead_diseases = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        prefetch: 'api/diseases'
    });

    const typeahead_preds = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        prefetch: 'api/predictive_implications'
    });

    const typeahead_therapies = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        prefetch: 'api/therapies'
    });

    $('.typeahead').typeahead({
        hint: true,
        highlight: true,
        minLength: 1,
    },
    {
        name: 'features',
        source: typeahead_features,
        limit: 3,
        templates: {
            header: '<h3 class="typeahead-category">Features</h3>'
        }
    },
    {
        name: 'diseases',
        source: typeahead_diseases,
        limit: 3,
        templates: {
            header: '<h3 class="typeahead-category">Diseases</h3>'
        }
    },
    {
        name: 'therapies',
        source: typeahead_therapies,
        limit: 3,
        templates: {
            header: '<h3 class="typeahead-category">Therapies</h3>'
        }
    },
    {
        name: 'preds',
        source: typeahead_preds,
        limit: 3,
        templates: {
            header: '<h3 class="typeahead-category">Predictive Implication Levels</h3>'
        }
    }
    );

    $('#feature-input').bind('typeahead:select', function(ev, suggestion) {
        $('#feature-input').value += suggestion;
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
