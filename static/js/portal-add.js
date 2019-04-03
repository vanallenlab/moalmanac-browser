// load data objects from remote JSON
function getJSONSearchSet(url, category, callback) {
    $.getJSON(url, function(data) {
        let search_set = Object;
        search_set = [];
        $.each(data, function(index, value) {
            let new_datum = Object();
            new_datum.id = value;
            new_datum.text = value;

            search_set.push(new_datum);
        });

        callback(search_set);
    });
}

getJSONSearchSet('api/features', 'feature', function(features) {
    $('#gene-input').select2({
        theme: 'bootstrap',
        multiple: false,
        tags: true,
        containerCssClass: 'select2-font',
        data: features
    });
});

$(document).ready(function() {
    // Selectors
    var implication_select = $('#implication-select')[0];
    var type_select = $('#type-select')[0];
    var therapy_select = $('#therapy-select')[0];
    var class_select = $('#class-select')[0];
    var effect_select = $('#effect-select')[0];
    var alteration_input = $('#alteration-input')[0];
    var source_input = $('#source-input')[0];
    var gene_input = $('#gene-input')[0];
    var email_input = $('#email-input')[0];

    // Reactions
    $('#btn-sub').click(function () {
        var therapy = therapy_select.value;
        var type = type_select.value;
        var implication = implication_select.value;
        var source = source_input.value;
        var gene = gene_input.value;
        var alt_class = class_select.value;
        var alteration = alteration_input.value;
        var effect = effect_select.value;
        var email = email_input.value;
        $.ajax({
            type: "POST",
            url: '/submit',
            data: {
                'therapy': therapy,
                'type': type,
                'implication': implication,
                'source': source,
                'gene': encodeURIComponent(gene),
                'effect': effect,
                'class': alt_class,
                'alteration': alteration,
                'email': encodeURIComponent(email)
            },
            success: function (response) {
                $('#success-panel').show();
                dict = JSON.parse(JSON.parse(response).message);
                $('#success-text').html("<b></br>Email: " + decodeURIComponent(dict.email) +
                    "</br>Therapy: " + dict.therapy +
                    "</br> Implication: " + dict.implication +
                    "</br> Gene: " + decodeURIComponent(dict.gene) +
                    "</br> Type: " + dict.type +
                    "</br> Class: " + dict.alt_class +
                    "</br> Effect: " + dict.effect +
                    "</br> Alteration: " + dict.alteration +
                    "</br> DOI: " + dict.source + "</b>");
                $('#error-panel').hide();
            },
            error: function (response) {
                $('#error-panel').show();
                $('#error-text').html(JSON.parse(response.responseText).message);
                $('#success-panel').hide();
            }
        });
    });
});
