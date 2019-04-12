// load data objects from remote JSON
function getJSONSearchSet(url, value_handler, callback) {
    // value_handler must return an dict with keys id and text
    $.getJSON(url, function(data) {
        let search_set = Object;
        search_set = [];
        $.each(data, function(index, value) {
            let new_datum = Object();
            let value_interp = value_handler(value);
            new_datum.id = value_interp.id;
            new_datum.text = value_interp.text;

            search_set.push(new_datum);
        });

        callback(search_set);
    });
}

function initSelect2Field(selector, data, tags=false, placeholder=null) {
    $(selector).select2({
        theme: 'bootstrap',
        multiple: false,
        tags: tags,
        placeholder: placeholder,
        containerCssClass: 'select2-font',
        width: '100%',
        data: data
    });
}

getJSONSearchSet('api/genes',
    function(value) { return {'id': value, 'text': value}; },
    function(genes) {
        initSelect2Field('.gene-select2', genes, true, 'Select gene');
    }
);

getJSONSearchSet('api/diseases',
    function(value) { return {'id': value, 'text': value}; },
    function(diseases) {
        initSelect2Field('#type-select', diseases, true, 'Select a disease');
    }
);

getJSONSearchSet('api/predictive_implications',
    function(value) { return {'id': value, 'text': value}; },
    function(diseases) {
        initSelect2Field('#implication-select', diseases, true,
            'Select a predictive implication level');
    }
);

getJSONSearchSet('api/therapies',
    function(value) { return {'id': value, 'text': value}; },
    function(diseases) {
        initSelect2Field('#therapy-select', diseases, true, 'Select a therapy');
    }
);

getJSONSearchSet('api/feature_definitions',
   function(value) { return {'id': value.feature_def_id, 'text': value.readable_name} },
   function(definitions) {
        initSelect2Field('#feature-definition-input', definitions, false, 'Select a feature');
    }
);

$.each($('.nongene-select2'), function(index, element) {
    let feature_def_id = element.dataset.featureDefId;
    let attribute_def_id = element.dataset.attributeDefId;
    getJSONSearchSet(
        'api/distinct_attribute_values/' + attribute_def_id,
        function (value) { return {'id': value, 'text': value}; },
        function (attributes) {
            initSelect2Field('#' + feature_def_id + '-' + attribute_def_id + '-input',
                attributes, true, 'Select or enter attribute');
        });
});

$(document).ready(function() {
    $('#feature-definition-input').change(function() {
        $('.add-feature-row').hide();
        $('.active-attribute').removeClass('active-attribute');

        let selected_row = $('#feature-' + $('#feature-definition-input').val() + '-row');
        selected_row.fadeIn();
        selected_row.find('.attribute-select2').addClass('active-attribute');
    });

    // Reactions
    $('#btn-sub').click(function () {
        let submission_values = {
            'source': $('#source-input').val(),
            'type': $('#type-select').val(),
            'feature_id': $('#feature-definition-input').val(),
            'therapy': $('#therapy-select').val(),
            'implication': $('#implication-select').val(),
            'email': encodeURIComponent($('#email-input').val())
        };

        $('.active-attribute').each(function(index, element) {
            submission_values['attribute-' + element.dataset.attributeDefId] = element.value;
        });

        $.ajax({
            type: "POST",
            url: '/submit',
            data: submission_values,
            success: function (response) {
                $('#success-panel').show();
                let dict = JSON.parse(JSON.parse(response).message);
                $('#success-text').html("<b></br>Email: " + decodeURIComponent(dict.email) +
                    "</br>Therapy: " + dict.therapy +
                    "</br> Implication: " + dict.implication +
                    "</br> Feature: " + dict.feature_name +
                    "</br> Source: " + dict.source + "</b>");
                $('#error-panel').hide();
            },
            error: function (response) {
                console.log(response);
                $('#error-panel').show();
                $('#error-text').html(JSON.parse(response.responseText).message);
                $('#success-panel').hide();
            }
        });
    });
});
