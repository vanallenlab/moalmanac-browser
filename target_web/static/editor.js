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
            row_count_placeholder: '{{row-count-placeholder}}',
        });
    });
});
