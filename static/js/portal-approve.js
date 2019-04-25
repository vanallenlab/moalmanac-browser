renderTable = function () {
    $('.results-table').DataTable({
        ordering: false,
        paging: true,
        searching: false
    });
}

renderTable();

// Approve the submission as it currently looks. This will lead to the submission appearing in search results.
$('.btn-approve').click(function (e) {
    let button = $(e.currentTarget);
    let button_data = button.data();
    let assertion_id = button_data.id;
    $.get('/approve_submission?assertion_id=' + assertion_id).done(function (data) {
        if (JSON.parse(data).success == true) {
            // Reload page
            location.reload();
        } else {
            alert("Something went wrong -- submission could not be approved.")
        }
    });
});

// Delete the submission forever.
$('.btn-delete').click(function (e) {
    let button = $(e.currentTarget);
    let button_data = button.data();
    let assertion_id = button_data.id;
    let gene = button_data.gene;
    let disease = button_data.disease;
    let r = confirm("Really delete submission for " + gene + " in " + disease + "?");
    if (r == true) {
        $.get('/delete_submission?assertion_id=' + assertion_id).done(function (data) {
            if (JSON.parse(data).success == true) {
                // Reload page
                location.reload();
            } else {
                alert("Something went wrong -- submission could not be deleted.")
            }
        });
    }
});

// Enable editing of field upon click.
$('.editable').click(function (e) {
    let td = $(e.currentTarget);
    let currentValue = td.data().val;
    let attr = td.data().attr;
    let assertionId = td.data().assertion_id;
    let textFieldType = td.data().type == 'text'? 'input' : 'textarea rows="5"';
    let optionalDoi = td.data().doi? td.data().doi: null;
    let placeholder = td.data().placeholder? td.data().placeholder : currentValue;

    // Replace the td's contents with a newly created input element
    let html_input_element = '<' + textFieldType + ' class="input" data-attr="' + attr + ' data-assertion_id="' + assertionId + '" type="text" placeholder="' + placeholder + '">'
    td.html(html_input_element);

    // Remove the click listener from this td so that we can type in the newly created input element at will
    td.removeClass('editable');
    td.unbind('click');

    // Put the cursor live on the input that just was created
    $('.input').focus();

    // An on-the-fly function to allow for submitting the input's contents to the backend upon hitting 'Enter'
    $('.input').keyup(function (e) {
        if (e.key == "Enter") {
            e.preventDefault();
            let newValue = e.currentTarget.value;
            $.ajax({
              type: "POST",
              url: '/amend',
              data: {
                'attribute_name': attr,
                'assertion_id': assertionId,
                'current_value': currentValue,
                'new_value': newValue,
                'doi': optionalDoi
              },
              success: function (response) {
                // Reload page
                location.reload();
              },
              error: function (response) {
                alert("Update failed");
              }
            });
        }
    });

    $('.input').blur(function (e) {
        // Clear any edits if the user clicks or tabs away from the text field without hitting enter
        location.reload();
    });
});