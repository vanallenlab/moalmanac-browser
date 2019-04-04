const cache_expiry = 1000*60*5; // cache expiration time in milliseconds

$(document).ready(function() {
    $('.search').select2({
        theme: 'bootstrap',
        multiple: true,
        containerCssClass: 'select2-font',
    });
});

function escapeRegexStr(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// check if a given token is in the ?s= or &s= search parameters
function tokenInSearchParams(token) {
    let search_str = window.location.search;
    search_str = search_str.replace(/\+/g, ' ');
    search_str = decodeURIComponent(search_str);
    search_str = search_str.replace(/(?:"|')/g, '');

    console.log(search_str);
    const search_regex = new RegExp('s=' + escapeRegexStr(token) + '(?:&|\\?|\\s*\\[|$)');
    return !(search_str.match(search_regex) == null);
}

// load data objects from remote JSON
function getJSONSearchSet(url, category, callback) {
    return $.getJSON(url, function(data) {
        let search_set = Object;
        search_set = [];
        $.each(data, function(index, value) {
            let new_datum = Object();
            new_datum.id = '"' + value + '"';
            new_datum.text = value;
            new_datum.category = category;

            search_set.push(new_datum);
        });

        callback(search_set);
    });
}

let search_space = localStorage.getItem('search_space');
let search_space_timestamp = parseInt(localStorage.getItem('search_space_timestamp'));
const cache_expiry_threshold = Date.now() - cache_expiry;

if (search_space && search_space_timestamp > cache_expiry_threshold) {
    search_space = JSON.parse(search_space);
    load_select2_data();
} else {
    search_space = [];

    let features = Object(), diseases = Object(), therapies = Object(), preds = Object();
    features.text = 'Features';
    diseases.text = 'Diseases';
    therapies.text = 'Therapies';
    preds.text = 'Predictive Implications';

    $.when(
            getJSONSearchSet('api/features', 'feature', function (data) {
                features.children = data;
            }),
            getJSONSearchSet('api/diseases', 'disease', function (data) {
                diseases.children = data;
            }),
            getJSONSearchSet('api/therapies', 'therapy', function (data) {
                therapies.children = data;
            }),
            getJSONSearchSet('api/predictive_implications', 'pred', function (data) {
                preds.children = data;
            })
    ).then(function() {
        search_space.push(features);
        search_space.push(diseases);
        search_space.push(therapies);
        search_space.push(preds);

        localStorage.setItem('search_space', JSON.stringify(search_space));
        localStorage.setItem('search_space_timestamp', Date.now().toString());
        load_select2_data();
    });
}

function addCategoryClass(data, container) {
    if (data.category) {
        $(container).addClass('select2-category-' + data.category);
    }

    return data.text;
}

function load_select2_data() {
    $.each(search_space, function(index, category) {
        $.each(category.children, function(index, child) {
            child.selected = tokenInSearchParams(child.text);
        });
    });

    $(document).ready(function() {
        $('.search').select2({
            'data': search_space,
            'templateSelection': addCategoryClass
        });
    });
}
