$(document).ready(function() {
	$('[data-toggle="tooltip"]').tooltip();
	$('.browse-dropdown').on('change', function() { this.form.submit() })
});

var substring_matcher = function(strs) {
  return function findMatches(q, cb) {
    var matches, substringRegex;

    matches = [];
    substrRegex = new RegExp(q, 'i');
    $.each(strs, function(i, str) {
      if (substrRegex.test(str)) {
        matches.push(str);
      }
    });

    cb(matches);
  };
};

if ($('.typeahead')) {
    $('.typeahead').typeahead({
        hint: true,
        highlight: true,
        minLength: 1
    },
    {
        name: 'typeahead_genes',
        source: substring_matcher(typeahead_genes)
    });
}

$('#gene-input').bind('typeahead:select', function(ev, suggestion) {
    $('#gene-input').value = suggestion;
    this.form.submit();
});

$(document).ready(function(){
    if ($('.results-table').DataTable) {
        $('.results-table').DataTable({
            ordering: true,
            paging: true,
            searching: false
        });
    }
});
