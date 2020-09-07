'use strict';
function delete_prediction(e) {

    var aux = e.parentElement;

    var padre = aux.parentElement;
    padre.removeChild(aux);
};


; (function (document, window, index) {
    // feature detection for drag&drop upload
    var isAdvancedUpload = function () {
        var div = document.createElement('div');
        return (('draggable' in div) || ('ondragstart' in div && 'ondrop' in div)) && 'FormData' in window && 'FileReader' in window;
    }();


    // applying the effect for every form
    var forms = document.querySelectorAll('.box');
    Array.prototype.forEach.call(forms, function (form) {
        var input = form.querySelector('input[type="file"]'),
            label = form.querySelector('label'),
            errorMsg = form.querySelector('.box__error span'),
            restart = form.querySelectorAll('.box__restart'),
            droppedFiles = false,
            showFiles = function (files) {
                label.textContent = files.length > 1 ? (input.getAttribute('data-multiple-caption') || '').replace('{count}', files.length) : files[0].name;
            },
            triggerFormSubmit = function () {
                var event = document.createEvent('HTMLEvents');
                event.initEvent('submit', true, false);
                form.dispatchEvent(event);
            };

        // automatically submit the form on file select
        input.addEventListener('change', function (e) {
            showFiles(e.target.files);
        });

        // drag&drop files if the feature is available
        if (isAdvancedUpload) {
            form.classList.add('has-advanced-upload'); // letting the CSS part to know drag&drop is supported by the browser

            ['drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop'].forEach(function (event) {
                form.addEventListener(event, function (e) {
                    // preventing the unwanted behaviours
                    e.preventDefault();
                    e.stopPropagation();
                });
            });
            ['dragover', 'dragenter'].forEach(function (event) {
                form.addEventListener(event, function () {
                    form.classList.add('is-dragover');
                });
            });
            ['dragleave', 'dragend', 'drop'].forEach(function (event) {
                form.addEventListener(event, function () {
                    form.classList.remove('is-dragover');
                });
            });
            form.addEventListener('drop', function (e) {
                droppedFiles = e.dataTransfer.files; // the files that were dropped
                showFiles(droppedFiles);
                //  document.getElementById("submit").click();

            });
        }

        // if the form was submitted
        form.addEventListener('submit', function (e) {
            // preventing the duplicate submissions if the current one is in progress
            if (form.classList.contains('is-uploading')) return false;

            form.classList.add('is-uploading');
            form.classList.remove('is-error');

            e.preventDefault();

            // Adding files to form
            if (droppedFiles) {
                form.file.files = droppedFiles;
            }
            if (form.file.files.length > 0) {
                // gathering the form data
                var ajaxData = new FormData(form);

                // ajax request
                var ajax = new XMLHttpRequest();
                ajax.open(form.getAttribute('method'), form.getAttribute('action'), true);

                ajax.onload = function () {
                    form.classList.remove('is-uploading');
                    if (ajax.status >= 200 && ajax.status < 400) {

                        var data = JSON.parse(ajax.responseText);
                        var predictions = document.getElementById("predictions");

                        data.forEach((elem) => {
                            var elems = [];
                            for (var i = 0; i < elem.mask.length; i++) {
                                var item = `
                                <div class="d-flex flex-column align-items-center col-12 col-md"> 
                                    <img class="img-fluid" height="350" width="350" src="data:image/png;base64,${elem.mask[i].mask_data}"/>
                                    <div class="text-primary font-weight-bold">${elem.mask[i].model_name}</div>
                                </div>
                            `;
                                elems.push(item);
                            }

                            const prediction = `
                            <div class="d-flex flex-column position-relative justify-content-around my-4 flex-wrap border border-primary border-3 p-3 rounded">
                                <div class="delete d-flex position-absolute justify-content-center align-items-center text-danger" onclick="delete_prediction(this)"><i class="fas fa-trash-alt"></i></div>
                                <div class="d-flex flex-column align-items-center"> 
                                    <img class="img-fluid" height="350" width="350" src="data:image/png;base64,${elem.image}"/>
                                    <div class="text-primary font-weight-bold">${elem.filename}</div>
                                </div>
                                <div class="row"> 
                                    ${elems.join("")}
                                </div>
                            </div>
                         `;




                            predictions.innerHTML += prediction;
                        });

                        label.innerHTML = `<strong>Choose files</strong><span class="box__dragndrop"> or drag them
                here</span>.`;

                    }
                    else {
                        alert('Error. Please, contact the webmaster!');
                    }
                };

                ajax.onerror = function () {
                    form.classList.remove('is-uploading');
                    alert('Error. Please, try again!');
                };

                ajax.send(ajaxData);
            } else {
                form.classList.remove('is-uploading');
                alert('You must select a file before submit!');
            }
        });


        // restart the form if has a state of error/success
        Array.prototype.forEach.call(restart, function (entry) {
            entry.addEventListener('click', function (e) {
                e.preventDefault();
                form.classList.remove('is-error', 'is-success');
                input.click();
            });
        });

        // Firefox focus bug fix for file input
        input.addEventListener('focus', function () { input.classList.add('has-focus'); });
        input.addEventListener('blur', function () { input.classList.remove('has-focus'); });

    });
}(document, window, 0));