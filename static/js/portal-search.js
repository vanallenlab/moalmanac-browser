function addCategoryClass(data, container) {
    // Select2 does not allow specification of fields other than id and text in the programmatically-added pre-
    // selected options. The category for these options is instead stored in their dataset.
    const category = data.category || data.element.dataset.category;
    if (category) {
        $(container).addClass('select2-category-' + category);
    }

    return data.text;
}

function escapeRegexStr(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// check if a given token is in the ?s= or &s= search parameters
function tokenInSearchParams(token) {
    let search_str = window.location.search;
    search_str = search_str.replace(/\+/g, ' ');
    search_str = decodeURIComponent(search_str);
    search_str = search_str.replace(/(?:["'])/g, '');

    const search_regex = new RegExp('s=' + escapeRegexStr(token) + '(?:&|\\?|\\s*\\[|$)');
    return !(search_str.match(search_regex) == null);
}

$(document).ready(function () {
    const select2_search = $('#search');
    select2_search.select2({
        theme: 'bootstrap',
        multiple: true,
        templateSelection: addCategoryClass,
        containerCssClass: 'select2-font',
        ajax: {
            url: 'api/select2_search',
            dataType: 'json',
            data: function (params) {
                return {s: params.term};
            }
        }
    });

    let query_string_regex = /[?&]s=([^&#]*)/g;
    let value_regex = /([^[]*)\[([^\]]*)]/g;

    let query_string_match = query_string_regex.exec(window.location.search);
    while (query_string_match != null) {
        // Browsers replace spaces in query parameters with the + symbol, but decodeURIComponent does not decode the +
        // symbol. We must first replace it before decoding the string.
        let values = decodeURIComponent(query_string_match[1].replace(/\+/g, ' '));
        let value_match = value_regex.exec(values);
        while (value_match != null) {
            let readable_value = value_match[1].replace(/"/g, '');
            let id = value_match[0];
            let category = value_match[2];

            let option = new Option(readable_value, id, true, true);
            option.dataset.category = category;

            select2_search.append(option).trigger('change');
            select2_search.trigger({
                type: 'select2:select',
                params: {data: {'id': id, 'text': readable_value}}
            });

            value_match = value_regex.exec(values);
        }

        query_string_match = query_string_regex.exec(window.location.search);
    }
});
