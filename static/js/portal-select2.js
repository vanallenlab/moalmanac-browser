// check if a given token is in the ?s= or &s= search parameters
function tokenInSearchParams(token) {
    token = encodeURIComponent(token);
    token = token.replace(/%20/g, '\\+'); // spaces are converted to + signs in URLs
    const search_regex = new RegExp('s=' + token + '(?:&|\\?|$)');
    return !(window.location.search.match(search_regex) == null);
}

// load data objects from remote JSON
function getJSONSearchSet(url, category, callback) {
    $.getJSON(url, function(data) {
        let search_set = Object;
        search_set = [];
        $.each(data, function(index, value) {
            let new_datum = Object();
            new_datum.id = value;
            new_datum.text = value;
            new_datum.selected = tokenInSearchParams(value);

            search_set.push(new_datum);
        });

        callback(search_set);
    });
}

let search_space = []

let features = Object();
features.text = 'Features';
getJSONSearchSet('api/features', 'feature', function(data) {features.children = data;});
search_space.push(features);

let diseases = Object();
diseases.text = 'Diseases';
getJSONSearchSet('api/diseases', 'disease', function(data) {diseases.children = data;});
search_space.push(diseases);

let therapies = Object();
therapies.text = 'Therapies';
getJSONSearchSet('api/therapies', 'therapy', function(data) {therapies.children = data;});
search_space.push(therapies);

let preds = Object();
preds.text = 'Predictive Implications';
getJSONSearchSet('api/predictive_implications', 'pred. implication',
    function(data) {preds.children = data;});
search_space.push(preds);

$(document).ajaxStop(function() {
    $('.search').select2({
        theme: 'bootstrap',
        multiple: true,
        containerCssClass: 'select2-font',
        data: search_space
    });
})

