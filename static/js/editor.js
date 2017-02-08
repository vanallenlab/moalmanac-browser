$(function() {
    $('.repeat').each(function() {
        $(this).repeatable_fields({
            wrapper: '.repeat-wrapper',
            container: '.repeat-container',
            row: '.repeat-row',
            add: '.repeat-add',
            remove: '.repeat-remove',
            move: '.repeat-move',
            template: '.repeat-template',
            after_add: function(container, new_row, default_after_add) {
                $('form').parsley().destroy();
                $('form').parsley();
                default_after_add(container, new_row);
            },
            row_count_placeholder: '__row-count-placeholder__',
        });
    });
});

window.Parsley.on('field:validated', function(fieldInstance) {
    if(fieldInstance.$element.is(':hidden')) {
        fieldInstance._ui.$errorsWrapper.css('display', 'block');
        fieldInstance.validationResult = true;

        return true;
    }
});

$('a.editor-add-item').click(function(e) {
    e.preventDefault();
})

$('#assertion-form').on('submit', function(e) {
    //e.preventDefault();

    var form = $(this);
    return form.parsley().validate();
})
