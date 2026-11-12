// ---------------------------------------------------------------
// tasks/static/tasks/js/app.js
// Small browser-side helpers. The SERVER still checks everything:
// these only give faster, friendlier feedback.
// Loaded with "defer", so the page HTML already exists when this runs.
// ---------------------------------------------------------------

(function () {
    'use strict';

    // 1. CONFIRMATION before dangerous actions.
    //    Any <form data-confirm="Question?"> asks first; "Cancel" stops it.
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();   // user said Cancel: do not send the form
            }
        });
    });

    // 2. TASK FORM checks (create / edit page).
    var taskForm = document.getElementById('task-form');
    if (taskForm) {
        var title = document.getElementById('id_title');
        var due = document.getElementById('id_due_date');
        // For an edit, the date the task had when the page opened ("" for a new task).
        var originalDue = taskForm.dataset.originalDueDate || '';
        var today = localToday();

        // New task: the calendar picker greys out past days.
        if (due && !originalDue) {
            due.min = today;
        }

        taskForm.addEventListener('submit', function (event) {
            clearErrors(taskForm);
            var ok = true;

            // The browser already blocks an EMPTY title ("required");
            // this also catches a title of only spaces.
            if (title && title.value.trim() === '') {
                showError(title, 'Please enter a title.');
                ok = false;
            }

            // Same rule as the server: a NEW or CHANGED date may not be in the past.
            // Dates as "YYYY-MM-DD" text compare correctly with < and >.
            if (due && due.value && due.value !== originalDue && due.value < today) {
                showError(due, 'Due date cannot be in the past.');
                ok = false;
            }

            if (!ok) {
                event.preventDefault();   // keep the user on the page to fix it
            }
        });
    }

    // 3. STOP DOUBLE SUBMITS: after a form is sent, disable its button.
    //    Registered LAST, so it only runs if steps 1-2 did not cancel the submit.
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (event.defaultPrevented) {
                return;
            }
            var button = event.submitter || form.querySelector('button[type="submit"]');
            if (button) {
                button.dataset.originalText = button.textContent;
                button.textContent = 'Please wait...';
                button.disabled = true;
            }
        });
    });

    // When the user comes BACK to a page (browser Back button), re-enable buttons.
    window.addEventListener('pageshow', function () {
        document.querySelectorAll('button[disabled]').forEach(function (button) {
            button.disabled = false;
            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
            }
        });
    });

    // ---------- helper functions ----------

    // Today's date as "YYYY-MM-DD" in the user's own time zone.
    function localToday() {
        var d = new Date();
        d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
        return d.toISOString().slice(0, 10);
    }

    // Show a red message under an input and mark it invalid.
    function showError(input, message) {
        var p = document.createElement('p');
        p.className = 'js-error';
        p.textContent = message;          // textContent (not innerHTML): safe from HTML injection
        input.insertAdjacentElement('afterend', p);
        input.setAttribute('aria-invalid', 'true');
        input.focus();
    }

    // Remove messages from a previous attempt.
    function clearErrors(form) {
        form.querySelectorAll('.js-error').forEach(function (el) { el.remove(); });
        form.querySelectorAll('[aria-invalid]').forEach(function (el) { el.removeAttribute('aria-invalid'); });
    }
})();
