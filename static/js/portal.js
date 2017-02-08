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

$('.typeahead').typeahead({
	hint: true,
	highlight: true,
	minLength: 1
},
{
	name: 'typeahead_genes',
	source: substring_matcher(typeahead_genes)
})
